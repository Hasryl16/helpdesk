"""Demo data: python -m app.seed  (safe to run again; existing businesses are skipped)."""

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Business, Message, Ticket, User
from app.security import hash_password
from app.services.auth import slugify

PASSWORD = "password123"

DEMO = [
    {
        "business": "Toko Maju",
        "domain": "tokomaju.com",
        "admin": "Rina",
        "agent": "Budi",
        "customers": ["Andi", "Sari"],
        "tickets": [("Pesanan belum sampai", "pengiriman"), ("Barang yang diterima rusak", "produk")],
    },
    {
        "business": "Klinik Sehat",
        "domain": "kliniksehat.com",
        "admin": "Dewi",
        "agent": "Eko",
        "customers": ["Fajar", "Gita"],
        "tickets": [("Jadwal dokter berubah", "jadwal"), ("Tagihan tidak sesuai", "pembayaran")],
    },
]


def seed() -> None:
    password_hash = hash_password(PASSWORD)
    with SessionLocal() as db:
        for demo in DEMO:
            slug = slugify(demo["business"])
            if db.scalar(select(Business.id).where(Business.slug == slug)):
                print(f"skip {demo['business']}: already seeded")
                continue

            business = Business(name=demo["business"], slug=slug)

            def user(name: str, role: str, email_name: str) -> User:
                return User(
                    business=business,
                    name=name,
                    email=f"{email_name}@{demo['domain']}",
                    password_hash=password_hash,
                    role=role,
                )

            agent = user(demo["agent"], "agent", "agent")
            customers = [user(name, "customer", f"customer{i}") for i, name in enumerate(demo["customers"], 1)]
            db.add_all([user(demo["admin"], "admin", "admin"), agent, *customers])
            db.flush()

            (open_subject, open_category), (busy_subject, busy_category) = demo["tickets"]
            open_ticket = Ticket(
                business_id=business.id,
                customer_id=customers[0].id,
                subject=open_subject,
                category=open_category,
                priority="high",
            )
            busy_ticket = Ticket(
                business_id=business.id,
                customer_id=customers[1].id,
                assigned_agent_id=agent.id,
                status="in_progress",
                subject=busy_subject,
                category=busy_category,
                priority="medium",
            )
            db.add_all([open_ticket, busy_ticket])
            db.flush()
            db.add_all(
                [
                    Message(ticket_id=open_ticket.id, sender_id=customers[0].id, body="Halo, mohon dibantu."),
                    Message(ticket_id=busy_ticket.id, sender_id=customers[1].id, body="Halo, mohon dibantu."),
                    Message(ticket_id=busy_ticket.id, sender_id=agent.id, body="Baik, sedang kami cek."),
                ]
            )
            db.commit()
            print(f"seeded {demo['business']}")


if __name__ == "__main__":
    seed()
