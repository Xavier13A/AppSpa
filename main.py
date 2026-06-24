from fastapi import FastAPI, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- BASE DE DATOS ---
DATABASE_URL = "sqlite:///./spa_database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    service = Column(String(100))
    date = Column(String(50))
    time = Column(String(50))

    __table_args__ = (UniqueConstraint('date', 'time', name='_date_time_uc'),)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

app = FastAPI(title="Xavier Spa System")

# =====================================================================
# 1. ENTORNO DEL CLIENTE (PORTADA Y RESERVAS)
# =====================================================================
HTML_CLIENTE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xavier Premium Spa</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #00796b; --secondary: #004d40; --bg: #f4f7f6; }
        body { font-family: 'Poppins', sans-serif; margin: 0; background-color: var(--bg); color: #333; }
        header { background: linear-gradient(rgba(0,121,107,0.85), rgba(0,121,107,0.85)), url('https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1350&q=80'); 
                 background-size: cover; background-position: center; height: 35vh; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; }
        h1 { font-family: 'Playfair Display', serif; font-size: 2.8rem; margin: 0; }
        .services-section { padding: 40px 20px; max-width: 1200px; margin: 0 auto; text-align: center; }
        .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 25px; margin-top: 30px; }
        .card { background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); }
        .card img { width: 100%; height: 160px; object-fit: cover; }
        .card-body { padding: 20px; }
        .price { color: var(--primary); font-weight: bold; font-size: 1.2rem; margin: 10px 0; }
        .btn { display: inline-block; padding: 10px 25px; border-radius: 30px; text-decoration: none; font-weight: 600; background: var(--primary); color: white; transition: 0.3s; border: none; cursor: pointer; }
        .btn:hover { background: var(--secondary); }
    </style>
</head>
<body>
    <header>
        <h1>Xavier Spa & Estética</h1>
        <p>Reserva tu turno de atención al instante</p>
    </header>

    <section class="services-section">
        <h2>Selecciona tu Servicio</h2>
        <div class="services-grid">
            <div class="card">
                <img src="https://images.unsplash.com/photo-1621605815971-fbc98d665033?auto=format&fit=crop&w=500&q=60">
                <div class="card-body"><h3>Corte de Cabello</h3><p class="price">$15.00</p><a href="/book?service=Corte%20de%20Cabello" class="btn">Agendar</a></div>
            </div>
            <div class="card">
                <img src="https://images.unsplash.com/photo-1519823551278-64ac92734fb1?auto=format&fit=crop&w=500&q=60">
                <div class="card-body"><h3>Spa de Rostro</h3><p class="price">$40.00</p><a href="/book?service=Spa%20de%20Rostro" class="btn">Agendar</a></div>
            </div>
            <div class="card">
                <img src="https://images.unsplash.com/photo-1604654894610-df4906db21ac?auto=format&fit=crop&w=500&q=60">
                <div class="card-body"><h3>Spa de Uñas</h3><p class="price">$20.00</p><a href="/book?service=Spa%20de%20Unas" class="btn">Agendar</a></div>
            </div>
            <div class="card">
                <img src="https://images.unsplash.com/photo-1522337660859-02fbefca4702?auto=format&fit=crop&w=500&q=60">
                <div class="card-body"><h3>Pedicura Completa</h3><p class="price">$25.00</p><a href="/book?service=Pedicura" class="btn">Agendar</a></div>
            </div>
        </div>
    </section>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(): return HTML_CLIENTE

@app.get("/book", response_class=HTMLResponse)
async def booking_form(service: str = "General", msg: str = ""):
    error_banner = f"<div style='color:#d32f2f; font-weight:bold; margin-bottom:15px; background:#ffcdd2; padding:10px; border-radius:5px;'>⚠️ {msg}</div>" if msg else ""
    return f"""
    <html>
    <head><style>
        body {{ font-family: sans-serif; background: #f4f7f6; text-align: center; padding: 50px; }}
        form {{ background: white; padding: 30px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: left; width: 100%; max-width: 350px; }}
        label {{ font-weight: bold; display: block; margin-top: 12px; color: #333; }}
        input, select {{ display: block; width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #ddd; box-sizing: border-box; }}
        button {{ background: #00796b; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; margin-top: 25px; font-weight: bold; cursor: pointer; font-size: 1rem; }}
    </style></head>
    <body>
        <h2>Agendar {service}</h2>
        {error_banner}
        <form action="/book" method="post">
            <input type="hidden" name="service" value="{service}">
            <label>Tu Nombre y Apellido:</label>
            <input type="text" name="name" required placeholder="Ej. Carlos Mendoza">
            <label>Selecciona el Día:</label>
            <input type="date" name="date" required>
            <label>Selecciona el Horario:</label>
            <select name="time" required>
                <option value="09:00">09:00 AM</option><option value="10:00">10:00 AM</option>
                <option value="11:00">11:00 AM</option><option value="12:00">12:00 PM</option>
                <option value="14:00">02:00 PM</option><option value="15:00">03:00 PM</option>
                <option value="16:00">04:00 PM</option><option value="17:00">05:00 PM</option>
            </select>
            <button type="submit">Confirmar Cita vía WhatsApp</button>
        </form>
    </body>
    </html>
    """

@app.post("/book")
async def save_booking(name: str = Form(...), service: str = Form(...), date: str = Form(...), time: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(Booking).filter(Booking.date == date, Booking.time == time).first()
    if existing:
        return RedirectResponse(url=f"/book?service={service}&msg=Este%20horario%20ya%20esta%20reservado.%20Por%20favor%20elige%20otra%20hora%20o%20dia.", status_code=303)
    
    new_booking = Booking(name=name, service=service, date=date, time=time)
    db.add(new_booking)
    db.commit()
    
    # NUEVO: Mensaje automatizado hacia tu número de WhatsApp Business real
    texto_whatsapp = f"Hola Xavier, acabo de agendar una cita en la App. Cliente: {name}. Servicio: {service}. Fecha: {date} a las {time}."
    texto_codificado = texto_whatsapp.replace(" ", "%20")
    return RedirectResponse(url=f"https://wa.me/593963692914?text={texto_codificado}", status_code=303)

# =====================================================================
# 2. ENTORNO INTERNO (RECEPTOR / AGENDA PRIVADA)
# =====================================================================
@app.get("/admin-agenda", response_class=HTMLResponse)
async def admin_panel(db: Session = Depends(get_db)):
    bookings = db.query(Booking).order_by(Booking.date, Booking.time).all()
    rows = "".join([f"<tr><td><b>{b.date}</b></td><td>{b.time}</td><td>{b.name}</td><td style='color:#00796b;font-weight:bold;'>{b.service}</td></tr>" for b in bookings])
    return f"""
    <html>
    <head>
        <title>Panel de Control - Spa</title>
        <style>
            body {{ font-family: sans-serif; background: #eceff1; padding: 40px; color: #37474f; }}
            .container {{ max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #cfd8dc; }}
            th {{ background: #1a237e; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📥 Panel del Receptor: Pedidos y Turnos</h1>
            <p>Lista organizada de citas para el control del negocio. Evita cruces automáticamente.</p>
            <table>
                <tr><th>Fecha</th><th>Hora</th><th>Nombre del Cliente</th><th>Servicio Solicitado</th></tr>
                {rows if rows else "<tr><td colspan='4' style='text-align:center;'>No hay citas registradas aún.</td></tr>"}
            </table>
        </div>
    </body>
    </html>
    """
