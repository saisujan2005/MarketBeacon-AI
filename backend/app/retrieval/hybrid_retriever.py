import logging
import uuid
from app.db.database import SessionLocal
from app.models.post import Post
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.daily_briefing import DailyBriefing
from app.models.research_report import ResearchReport
from app.retrieval.bm25_service import BM25Retriever
from app.embeddings.search_service import search_news
from app.retrieval.reranker import rerank

logger = logging.getLogger(__name__)


def hybrid_search(query, user_id: uuid.UUID = None, top_k=5, include_research_library=False):
    db = SessionLocal()
    try:
        # Posts are global scraped intelligence
        posts = db.query(Post).all()
        
        # Scope user data by user_id if provided
        if user_id:
            alerts = db.query(Alert).filter(Alert.user_id == user_id).all()
            notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
            briefings = db.query(DailyBriefing).filter(DailyBriefing.user_id == user_id).all()
            reports = db.query(ResearchReport).all() # Global or keep general
        else:
            alerts = db.query(Alert).all()
            notifications = db.query(Notification).all()
            briefings = db.query(DailyBriefing).all()
            reports = db.query(ResearchReport).all()

        documents = []
        lookup = {}

        # 1. Index Posts (News Intelligence)
        for post in posts:
            title = f"News: {post.title}"
            documents.append(title)
            
            company_tag = None
            if post.entities and isinstance(post.entities, dict):
                companies = post.entities.get("companies", [])
                if companies:
                    company_tag = companies[0]

            lookup[title] = {
                "title": post.title,
                "url": post.post_url or "",
                "source": f"News Source: {post.source_id or 'General News'}",
                "text": post.content or post.title,
                "document_id": str(post.id),
                "source_file": post.title,
                "company_name": company_tag,
                "document_type": "News",
                "chunk_index": 0,
                "similarity_score": 0.60
            }

        # 2. Index Smart Alerts
        for alert in alerts:
            title = f"Alert: {alert.title}"
            documents.append(title)
            lookup[title] = {
                "title": alert.title,
                "url": alert.post_url or "",
                "source": f"Smart Alert: {alert.event_type or 'General Alert'}",
                "text": alert.summary_text or alert.title,
                "document_id": str(alert.id),
                "source_file": alert.title,
                "company_name": None,
                "document_type": "Alert",
                "chunk_index": 0,
                "similarity_score": 0.60
            }

        # 3. Index Notifications
        for notif in notifications:
            title = f"Notification: {notif.title}"
            documents.append(title)
            lookup[title] = {
                "title": notif.title,
                "url": notif.post_url or "",
                "source": f"Watchlist Notification ({notif.keyword or 'General'})",
                "text": notif.title,
                "document_id": str(notif.id),
                "source_file": notif.title,
                "company_name": notif.keyword,
                "document_type": "Notification",
                "chunk_index": 0,
                "similarity_score": 0.60
            }

        # 4. Index Daily Briefings
        for dbf in briefings:
            title = f"Daily Briefing ({dbf.created_at.strftime('%Y-%m-%d')})"
            documents.append(title)
            text_body = f"Market Outlook: {dbf.outlook}\nMarket Summary: {dbf.market_summary}"
            lookup[title] = {
                "title": title,
                "url": "",
                "source": f"AI Daily Briefing - Outlook: {dbf.outlook or 'Neutral'}",
                "text": text_body,
                "document_id": str(dbf.id),
                "source_file": title,
                "company_name": None,
                "document_type": "Daily Briefing",
                "chunk_index": 0,
                "similarity_score": 0.60
            }

        # 5. Index Research Reports
        for rep in reports:
            title = f"Research Report: {rep.entity_name}"
            documents.append(title)
            report_text = rep.report_data.get("report_text", "") if rep.report_data else ""
            lookup[title] = {
                "title": title,
                "url": "",
                "source": f"Research Report: {rep.entity_name} (Rating: {rep.report_data.get('rating', 'NEUTRAL') if rep.report_data else 'NEUTRAL'})",
                "text": report_text,
                "document_id": str(rep.id),
                "source_file": title,
                "company_name": rep.entity_name,
                "document_type": "Research Report",
                "chunk_index": 0,
                "similarity_score": 0.60
            }

        if not documents:
            documents = ["MarketBeacon Finance Platform Overview"]
            lookup["MarketBeacon Finance Platform Overview"] = {
                "title": "MarketBeacon Finance Platform Overview",
                "url": "",
                "source": "System Default",
                "text": "MarketBeacon AI Dashboard for professional stock analysts and research.",
                "document_id": "00000000-0000-0000-0000-000000000000",
                "source_file": "Platform Overview",
                "company_name": None,
                "document_type": "System",
                "chunk_index": 0,
                "similarity_score": 0.50
            }

        # Run BM25 keyword matching
        bm25 = BM25Retriever(documents)
        bm25_results = bm25.search(query, top_k=10)

        # Run Vector Search on News collection
        vector_results = []
        try:
            vector_results = search_news(query)
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")

        combined = []

        # Process BM25 results
        for doc, score in bm25_results:
            combined.append({
                **lookup[doc],
                "score": float(score)
            })

        # Process Vector results
        for result in vector_results:
            payload_title = result.payload.get("title", "")
            lookup_title = f"News: {payload_title}"
            if lookup_title in lookup:
                item = dict(lookup[lookup_title])
                item["similarity_score"] = float(result.score)
                item["score"] = float(result.score)
                combined.append(item)
            else:
                combined.append({
                    "title": payload_title,
                    "url": result.payload.get("url", ""),
                    "source": f"Vector Search: {result.payload.get('source_id', 'Unknown')}",
                    "text": payload_title,
                    "document_id": None,
                    "source_file": payload_title,
                    "company_name": None,
                    "document_type": "News",
                    "chunk_index": 0,
                    "similarity_score": float(result.score),
                    "score": float(result.score)
                })

        # 6. Query Research Library Vector Collection (Deep Research Toggle)
        if include_research_library:
            try:
                from app.embeddings.qdrant_service import client as q_client, RESEARCH_COLLECTION_NAME
                from app.embeddings.embedder import generate_embedding
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                
                q_emb = generate_embedding(query)
                
                # Apply user isolation filter on Qdrant query if user_id is provided
                q_filter = None
                if user_id:
                    q_filter = Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=str(user_id))
                            )
                        ]
                    )
                
                q_res = q_client.search(
                    collection_name=RESEARCH_COLLECTION_NAME,
                    query_vector=q_emb,
                    query_filter=q_filter,
                    limit=12
                )
                for qr in q_res:
                    chunk_title = qr.payload.get("source_file", "Research Report")
                    unique_title = f"Doc Chunk: {chunk_title} (Idx: {qr.payload.get('chunk_index', 0)})"
                    chunk_text = qr.payload.get("text", "")
                    
                    doc_item = {
                        "title": unique_title,
                        "url": "",
                        "source": f"Research Library: {qr.payload.get('document_type', 'Document')}",
                        "text": chunk_text,
                        "document_id": qr.payload.get("document_id"),
                        "source_file": chunk_title,
                        "company_name": qr.payload.get("company_name"),
                        "document_type": qr.payload.get("document_type"),
                        "chunk_index": qr.payload.get("chunk_index"),
                        "similarity_score": float(qr.score),
                        "score": float(qr.score)
                    }
                    combined.append(doc_item)
            except Exception as e:
                logger.error(f"Failed to query Qdrant research collection in hybrid search: {e}")

        # Deduplicate matches by title (prefer higher score)
        unique = {}
        for item in combined:
            title = item["title"]
            if title not in unique:
                unique[title] = item
            else:
                if item["score"] > unique[title]["score"]:
                    unique[title] = item

        combined = list(unique.values())

        # Cross-Encoder Rerank
        reranked = rerank(query, combined)
        
        # Incorporate source quality weights in ranking
        from app.services.reliability_layer import get_source_tier_info
        for doc in reranked:
            doc_type = doc.get("document_type", "")
            src_label = doc.get("source", "")
            tier_info = get_source_tier_info(doc_type, src_label)
            
            doc["source_weight"] = tier_info["weight"]
            doc["source_tier"] = tier_info["tier"]
            doc["source_tier_label"] = tier_info["label"]
            doc["source_description"] = tier_info["description"]
            
            boost = 3.0 * tier_info["weight"]
            doc["adjusted_score"] = doc.get("rerank_score", 0.0) + boost

        # Sort combined results by adjusted score
        reranked_sorted = sorted(
            reranked,
            key=lambda x: x.get("adjusted_score", 0.0),
            reverse=True
        )
        return reranked_sorted[:top_k]
    finally:
        db.close()