from fastapi import FastAPI, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import urllib.parse
import json

# --- BASE DE DATOS PERMANENTE ---
DATABASE_URL = "sqlite://///tmp/spa_database.db"
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
async def index_root():
    return HTML_CLIENTE

@app.get("/book", response_class=HTMLResponse)
async def booking_form(service: str = "General", msg: str = "", db: Session = Depends(get_db)):
    error_banner = f"<div style='color:#d32f2f; font-weight:bold; margin-bottom:15px; background:#ffcdd2; padding:10px; border-radius:5px;'>⚠️ {msg}</div>" if msg else ""
    
    taken_slots = db.query(Booking.date, Booking.time).all()
    slots_dict = {}
    for d, t in taken_slots:
        if d not in slots_dict: slots_dict[d] = []
        slots_dict[d].append(t)
    
    taken_json = json.dumps(slots_dict)

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reservar Turno</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f7f6; text-align: center; padding: 15px; margin: 0; }}
            form {{ background: white; padding: 25px; border-radius: 16px; display: inline-block; box-shadow: 0 8px 24px rgba(0,0,0,0.08); text-align: left; width: 100%; max-width: 400px; box-sizing: border-box; }}
            label {{ font-weight: bold; display: block; margin-top: 15px; color: #333; font-size: 0.95rem; }}
            input[type="text"], input[type="date"] {{ display: block; width: 100%; padding: 12px; margin-top: 5px; border-radius: 8px; border: 1px solid #ddd; box-sizing: border-box; font-size: 1rem; }}
            
            /* GRAFICA DE HORARIOS EN MATRIZ (GRID) */
            .grid-horarios {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }}
            .slot-btn {{ padding: 12px 5px; text-align: center; border-radius: 8px; border: 2px solid #00796b; background: #e0f2f1; color: #004d40; font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 0.9rem; }}
            .slot-btn:hover {{ background: #00796b; color: white; }}
            
            /* Clase cuando el usuario selecciona una hora libre */
            .slot-btn.selected {{ background: #004d40 !important; color: white !important; border-color: #002d24 !important; box-shadow: 0 0 8px rgba(0,0,0,0.2); }}
            
            /* Clase cuando la hora ya está ocupada */
            .slot-btn.disabled {{ background: #eceff1 !important; color: #b0bec5 !important; border-color: #cfd8dc !important; cursor: not-allowed !important; text-decoration: line-through; }}
            
            button[type="submit"] {{ background: #00796b; color: white; border: none; padding: 14px; width: 100%; border-radius: 8px; margin-top: 30px; font-weight: bold; cursor: pointer; font-size: 1.1rem; box-shadow: 0 4px 12px rgba(0,121,107,0.3); }}
            button[type="submit"]:hover {{ background: #004d40; }}
            .info-dispo {{ font-size: 0.85rem; color: #555; margin-top: 5px; background: #e8f5e9; padding: 8px; border-radius: 6px; font-weight: 500; text-align: center; display: none; }}
        </style>
        <script>
            const ocupados = {taken_json};

            function seleccionarHora(btn, hora) {{
                if (btn.classList.contains('disabled')) return;
                
                // Deseleccionar el botón anterior
                document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
                
                // Seleccionar el actual
                btn.classList.add('selected');
                
                # Guardar el valor en el input oculto del formulario
                document.getElementById("time_hidden").value = hora;
            }}

            function actualizarGraficaHorarios() {{
                const fechaSeleccionada = document.getElementById("date_input").value;
                const infoBox = document.getElementById("info_slots");
                
                if (!fechaSeleccionada) {{
                    infoBox.style.display = "none";
                    return;
                }}

                const horasOcupadas = ocupados[fechaSeleccionada] || [];
                let disponibles = 0;

                // Buscar todos los botones de bloques de horas
                document.querySelectorAll('.slot-btn').forEach(btn => {{
                    const horaValor = btn.getAttribute('data-time');
                    
                    if (horasOcupadas.includes(horaValor)) {{
                        btn.classList.add('disabled');
                        btn.classList.remove('selected');
                    }} else {{
                        btn.classList.remove('disabled');
                        disponibles++;
                    }}
                }});

                // Limpiar la selección oculta al cambiar de día
                document.getElementById("time_hidden").value = "";
                document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));

                // Mostrar resumen visual informativo
                infoBox.style.display = "block";
                infoBox.innerText = `✅ Hay ${{disponibles}} horarios disponibles para esta fecha`;
            }}
        </script>
    </head>
    <body>
        <form action="/book" method="post">
            <h3 style="margin-top:0; color:#00796b; border-bottom:2px solid #e0f2f1; padding-bottom:10px;">🗓️ Agendar {service}</h3>
            {error_banner}
            
            <input type="hidden" name="service" value="{service}">
            <input type="hidden" id="time_hidden" name="time" required>
            
            <label>Tu Nombre y Apellido:</label>
            <input type="text" name="name" required placeholder="Ej. Orlando Xavier">
            
            <label>Selecciona el Día:</label>
            <input type="date" id="date_input" name="date" required onchange="actualizarGraficaHorarios()">
            
            <div id="info_slots" class="info-dispo"></div>
            
            <label style="margin-top:20px;">Selecciona un horario disponible:</label>
            <div class="grid-horarios">
                <div class="slot-btn" data-time="09:00" onclick="seleccionarHora(this, '09:00')">09:00 AM</div>
                <div class="slot-btn" data-time="10:00" onclick="seleccionarHora(this, '10:00')">10:00 AM</div>
                <div class="slot-btn" data-time="11:00" onclick="seleccionarHora(this, '11:00')">11:00 AM</div>
                <div class="slot-btn" data-time="12:00" onclick="seleccionarHora(this, '12:00')">12:00 PM</div>
                <div class="slot-btn" data-time="14:00" onclick="seleccionarHora(this, '14:00')">02:00 PM</div>
                <div class="slot-btn" data-time="15:00" onclick="seleccionarHora(this, '15:00')">03:00 PM</div>
                <div class="slot-btn" data-time="16:00" onclick="seleccionarHora(this, '16:00')">04:00 PM</div>
                <div class="slot-btn" data-time="17:00" onclick="seleccionarHora(this, '17:00')">05:00 PM</div>
            </div>
            
            <button type="submit">Confirmar Cita vía WhatsApp 🚀</button>
        </form>
    </body>
    </html>
    """

@app.post("/book")
async def save_booking(name: str = Form(...), service: str = Form(...), date: str = Form(...), time: str = Form(...), db: Session = Depends(get_db)):
    if not time:
        return RedirectResponse(url=f"/book?service={service}&msg=Por%20favor%20selecciona%20un%20bloque%20de%20horario.", status_code=303)
        
    existing = db.query(Booking).filter(Booking.date == date, Booking.time == time).first()
    if existing:
        return RedirectResponse(url=f"/book?service={service}&msg=Este%20horario%20ya%20esta%20reservado.%20Por%20favor%20elige%20otra%20hora%20o%20dia.", status_code=303)
    
    new_booking = Booking(name=name, service=service, date=date, time=time)
    db.add(new_booking)
    db.commit()
    
    texto_whatsapp = f"Hola Xavier, acabo de agendar una cita en la App. Cliente: {name}. Servicio: {service}. Fecha: {date} a las {time}."
    texto_seguro = urllib.parse.quote(texto_whatsapp)
    
    return RedirectResponse(url=f"https://wa.me/593963692914?text={texto_seguro}", status_code=303)

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
