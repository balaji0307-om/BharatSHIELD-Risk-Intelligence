"""
AI Risk Assistant Service: Strictly read-only, defense-oriented analysis.
Integrates Gemini LLM (when configured) with deterministic fallback,
rigorous prompt injection defense, and grounding exclusively on verified BharatSHIELD data.

HARD ARCHITECTURAL CONSTRAINT:
This service has ZERO write access to transaction, account, or monetary states.
It can only query, read, and explain existing risk engine data, alerts, cases, and transaction records.
"""

from typing import Dict, Any, Optional, List
import json
import re
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.config import settings
from backend.app.models.transaction import Transaction
from backend.app.models.risk_case import RiskScore, RiskFactor, RiskCase, AuditLog
from backend.app.models.alert import Alert

logger = logging.getLogger(__name__)

FORBIDDEN_ACTIONS = [
    "refund", "money movement", "transfer", "payout", "cancel transaction",
    "release hold", "approve transaction", "delete", "drop table", "execute",
    "chargeback", "settle", "freeze account", "unblock"
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) (instructions|directions|rules)",
    r"you are now (in|a) (developer|dan|jailbreak|unrestricted) mode",
    r"system prompt override",
    r"pretend (you are|to be)",
    r"disregard (safety|guardrails)",
    r"bypass (restrictions|filters)",
    r"act as an? (unrestricted|admin|god)"
]

class RiskAssistantService:
    """
    Read-only Risk Intelligence Assistant with LLM grounding and security guardrails.
    """

    @staticmethod
    def answer_query(db: Session, query: str, merchant_id: str = "MER_razorpay_001") -> Dict[str, Any]:
        cleaned_query = query.strip()
        lower_query = cleaned_query.lower()

        # 1. Prompt Injection Defense
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lower_query):
                return {
                    "response": (
                        "[SECURITY DEFENSE ACTIVATED] Prompt injection attempt detected. "
                        "BharatSHIELD AI operates strictly under deterministic safety parameters "
                        "and cannot deviate from its read-only merchant risk analysis role."
                    ),
                    "guardrail_status": "BLOCKED",
                    "grounded_data": None
                }

        # 2. Strict Action Guardrail Check (Forbidden Verbs)
        for forbidden in FORBIDDEN_ACTIONS:
            if re.search(r'\b' + re.escape(forbidden) + r'\b', lower_query):
                    return {
                        "response": (
                            f"[SECURITY GUARDRAIL TRIGGERED] BharatSHIELD AI Risk Assistant operates in strict "
                            f"read-only analytical mode. It cannot perform financial mutations, money movement, "
                            f"status reversals, or actions like '{forbidden}'. "
                            f"All operational changes must be executed by an authorized risk officer through manual review."
                        ),
                        "guardrail_status": "BLOCKED",
                        "grounded_data": None
                    }

        # 3. Grounded Context Retrieval
        context_data = RiskAssistantService._gather_grounded_context(db, cleaned_query, merchant_id)

        # 4. If transaction ID mentioned but not found, prevent hallucination
        txn_match = re.search(r'([0-9a-fA-F-]{8,36}|TXN-[0-9a-zA-Z]+)', query, re.IGNORECASE)
        if txn_match and not context_data.get("transaction"):
            return {
                "response": (
                    f"I don't have verified data for transaction '{txn_match.group(1)}'. "
                    "I cannot provide analysis without confirmed BharatSHIELD merchant records."
                ),
                "guardrail_status": "ANALYZED",
                "grounded_data": None
            }

        # 5. Attempt LLM Generation if GEMINI_API_KEY is configured
        if settings.GEMINI_API_KEY:
            try:
                llm_response = RiskAssistantService._query_gemini_llm(cleaned_query, context_data)
                if llm_response:
                    # Post-generation validation to ensure model didn't promise actions
                    for forbidden in FORBIDDEN_ACTIONS:
                        if re.search(r'\b' + re.escape(forbidden) + r'\b', llm_response.lower()):
                            if any(phrase in llm_response.lower() for phrase in ["i will", "processed", "executed", "authorized"]):
                                return {
                                    "response": "I can only analyze risk and explain findings; financial actions cannot be executed.",
                                    "guardrail_status": "BLOCKED",
                                    "grounded_data": context_data
                                }
                    return {
                        "response": llm_response,
                        "guardrail_status": "ANALYZED_LLM",
                        "grounded_data": context_data
                    }
            except Exception as e:
                logger.warning(f"Gemini LLM invocation failed, using deterministic fallback: {e}")

        # 6. Deterministic High-Quality Rule-Based Response Fallback
        return RiskAssistantService._deterministic_response(db, cleaned_query, context_data, merchant_id)

    @staticmethod
    def _gather_grounded_context(db: Session, query: str, merchant_id: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {"merchant_id": merchant_id}

        # Check for transaction ID in query
        txn_match = re.search(r'([0-9a-fA-F-]{8,36}|TXN-[0-9a-zA-Z]+)', query, re.IGNORECASE)
        if txn_match:
            raw_id = txn_match.group(1)
            txn = db.query(Transaction).filter(
                Transaction.merchant_id == merchant_id,
                Transaction.transaction_id.like(f"%{raw_id}%")
            ).first()

            if txn:
                score = db.query(RiskScore).filter(RiskScore.transaction_id == txn.transaction_id).first()
                factors = db.query(RiskFactor).filter(
                    RiskFactor.transaction_id == txn.transaction_id
                ).order_by(desc(RiskFactor.contribution)).all()

                case = db.query(RiskCase).filter(RiskCase.transaction_id == txn.transaction_id).first()

                context["transaction"] = {
                    "id": txn.transaction_id,
                    "amount": txn.amount,
                    "currency": txn.currency,
                    "payment_method": txn.payment_method,
                    "device_id": txn.device_id,
                    "location": txn.location,
                    "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,
                    "risk_score": score.risk_score if score else None,
                    "risk_level": score.risk_level if score else None,
                    "recommended_action": score.recommended_action if score else None,
                    "factors": [{"driver": f.display_name, "points": round(f.contribution, 1), "direction": f.direction} for f in factors[:5]],
                    "case_status": case.status if case else "No active case"
                }

        # Aggregate context metrics
        total_txns = db.query(Transaction).filter(Transaction.merchant_id == merchant_id).count()
        critical_count = db.query(RiskScore).join(
            Transaction, RiskScore.transaction_id == Transaction.transaction_id
        ).filter(
            Transaction.merchant_id == merchant_id,
            RiskScore.risk_score >= 75
        ).count()
        active_alerts = db.query(Alert).filter(
            Alert.merchant_id == merchant_id,
            Alert.is_acknowledged == False
        ).count()

        context["overview"] = {
            "total_transactions": total_txns,
            "critical_holds": critical_count,
            "active_alerts": active_alerts
        }

        return context

    @staticmethod
    def _query_gemini_llm(query: str, context: Dict[str, Any]) -> Optional[str]:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            system_instruction = (
                "You are BharatSHIELD AI Risk Assistant, an enterprise-grade defense-only payment fraud intelligence assistant. "
                "CRITICAL RULES:\n"
                "1. Strictly read-only: You have NO ability to execute refunds, approve transactions, transfer money, or release holds.\n"
                "2. Grounding: Answer ONLY based on the provided verified BharatSHIELD data. Do NOT invent transactions or metrics.\n"
                "3. If data is unavailable, state: 'I don't have enough verified data to answer that.'\n"
                "4. Be concise, structured, professional, and highlight SHAP risk drivers clearly."
            )

            prompt = f"Merchant Verified Context:\n{json.dumps(context, indent=2)}\n\nAnalyst Query: {query}"

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            return response.text
        except Exception as exc:
            logger.error(f"Error calling google-genai: {exc}")
            return None

    @staticmethod
    def _deterministic_response(db: Session, query: str, context: Dict[str, Any], merchant_id: str) -> Dict[str, Any]:
        lower = query.lower()

        # Specific transaction explanation
        if context.get("transaction"):
            t = context["transaction"]
            drivers_text = "\n".join([f"  • {f['driver']}: +{f['points']} risk points ({f['direction']})" for f in t["factors"]])

            response = (
                f"Risk Intelligence for Transaction {t['id'][:8]}...:\n\n"
                f"• Amount: ₹{t['amount']:,.2f} ({t['payment_method']})\n"
                f"• Risk Score: {t['risk_score']}/100 [{t['risk_level']}]\n"
                f"• Recommended Action: {t['recommended_action']}\n"
                f"• Investigation Case: {t['case_status']}\n\n"
                f"Top Contributing Risk Drivers (SHAP):\n{drivers_text or '  • Standard baseline telemetry.'}\n\n"
                f"Assessment: The combination of these features produced an elevated risk probability. "
                f"Analyst sign-off is required for resolution."
            )
            return {
                "response": response,
                "guardrail_status": "ANALYZED",
                "grounded_data": t
            }

        # Critical threats / alerts
        if any(w in lower for w in ["critical", "high risk", "today", "threat", "alert", "anomaly"]):
            ov = context.get("overview", {})
            return {
                "response": (
                    f"Merchant Threat Overview ({merchant_id}):\n\n"
                    f"• Critical Risk Transactions: {ov.get('critical_holds', 0)}\n"
                    f"• Active Unacknowledged Alerts: {ov.get('active_alerts', 0)}\n"
                    f"• Monitored Transactions: {ov.get('total_transactions', 0):,}\n\n"
                    f"Primary signals driving recent flags include high 5-minute velocity spikes, "
                    f"rapid geographic shifts, and newly detected device fingerprints."
                ),
                "guardrail_status": "ANALYZED",
                "grounded_data": ov
            }

        # General summary
        ov = context.get("overview", {})
        return {
            "response": (
                f"BharatSHIELD AI Risk Assistant (Active)\n\n"
                f"• Total Transactions Processed: {ov.get('total_transactions', 0):,}\n"
                f"• Active Critical Alerts: {ov.get('critical_holds', 0)}\n"
                f"• Architecture: XGBoost ML + SHAP Local Attribution + SHA-256 Audit Chain\n\n"
                f"Ask me to explain any transaction ('Why is TXN-XXX critical?'), inspect recent spikes, "
                f"or summarize merchant risk posture."
            ),
            "guardrail_status": "ANALYZED",
            "grounded_data": ov
        }
