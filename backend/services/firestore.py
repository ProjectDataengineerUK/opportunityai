from datetime import datetime, timezone
from google.cloud import firestore
from models import Opportunity


class FirestoreService:
    def __init__(self, project_id: str = ""):
        kwargs = {"project": project_id} if project_id else {}
        self.db = firestore.Client(**kwargs)
        self.col = self.db.collection("opportunities")

    def exists(self, external_id: str) -> bool:
        docs = self.col.where("external_id", "==", external_id).limit(1).get()
        return len(list(docs)) > 0

    def save(self, opportunity: Opportunity) -> str:
        doc_ref = self.col.document()
        data = opportunity.model_dump()
        data["id"] = doc_ref.id
        data["collected_at"] = datetime.now(timezone.utc)
        doc_ref.set(data)
        return doc_ref.id

    def list_opportunities(
        self,
        area: str | None = None,
        decision: str | None = None,
        source: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        query = self.col.order_by("score", direction=firestore.Query.DESCENDING)
        if area:
            query = query.where("area", "==", area)
        if decision:
            query = query.where("decision", "==", decision)
        if source:
            query = query.where("source", "==", source)
        docs = query.limit(limit).get()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]

    def get_opportunity(self, opportunity_id: str) -> dict | None:
        doc = self.col.document(opportunity_id).get()
        if not doc.exists:
            return None
        return {"id": doc.id, **doc.to_dict()}

    def update_opportunity(self, opportunity_id: str, fields: dict) -> None:
        self.col.document(opportunity_id).update(fields)
