import uvicorn
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# ==========================================
# 1. CONFIGURACIÓN DE LA BASE DE DATOS (SQLite)
# ==========================================
# SQLite guardará todo en un archivo local llamado 'spa.db' dentro de tu carpeta.
DATABASE_URL = "sqlite:///./spa.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. MODELOS DE BASE DE DATOS (ESCALABLES)
# ==========================================

# Tabla de Servicios (Tu Catálogo)
class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    duration = Column(Integer)  # Duración en minutos
    
    appointments = relationship("Appointment", back_populates="service")

# Tabla de Clientes (Pensada para tu futura Ficha Facial)
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String)
    skin_type = Column(String)  # Campo para el tipo de piel
    notes = Column(String)
    
    appointments = relationship("Appointment", back_populates="client")

# Tabla de Citas (Para agendar turnos)
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    date_time = Column(String)  
    status = Column(String, default="Pendiente")  
    
    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

# Crear las tablas automáticamente
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. DATOS INICIALES DEL SPA
# ==========================================
db = SessionLocal()
if db.query(Service).count() == 0:
    servicios_iniciales = [
        Service(name="Limpieza Facial Profunda", price=45.0, duration=60, description="Exfoliación, extracción de impurezas, vapor de ozono y mascarilla hidronutritiva para devolverle la luminosidad a tu piel."),
        Service(name="Masaje Relajante Aromático", price=60.0, duration=50, description="Masaje corporal completo con aceites esenciales templados de lavanda y técnicas de relajación profunda."),
        Service(name="Tratamiento Hidratante Premium", price=55.0, duration=45, description="Ideal para pieles deshidratadas. Incluye mascarilla de ácido hialurónico y masaje facial tensor.")
    ]
    db.add_all(servicios_iniciales)
    db.commit()
db.close()

# ==========================================
# 4. APLICACIÓN WEB (FASTAPI)
# ==========================================
app = FastAPI(title="Spa App")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Estilo Visual con Tailwind CSS (Verde Salvia y Minimalista)
HTML_HEADER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌿 Serene Spa - Catálogo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=Montserrat:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Montserrat', sans-serif; background-color: #f4f6f4; }
        h1, h2, h3 { font-family: 'Playfair Display', serif; }
    </style>
</head>
<body class="min-h-screen text-slate-800">
    <nav class="bg-emerald-900 text-white py-5 px-6 shadow-md">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-semibold tracking-wide flex items-center gap-2">
                <span>🌿</span> Serene Spa
            </a>
            <div class="flex gap-6 text-sm font-medium">
                <a href="/" class="hover:text-amber-200 transition">Catálogo</a>
                <a href="/appointments" class="hover:text-amber-200 transition bg-amber-700/50 px-3 py-1.5 rounded-lg">Citas de Hoy</a>
            </div>
        </div>
    </nav>
"""

HTML_FOOTER = """
    <footer class="bg-stone-100 border-t border-stone-200 py-8 mt-12 text-center text-sm text-stone-500">
        <p>© 2026 Serene Spa. Catálogo Web Escalable.</p>
    </footer>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    services = db.query(Service).all()
    catalog_cards = ""
    for s in services:
        catalog_cards += f"""
        <div class="bg-white rounded-2xl shadow-sm border border-emerald-100 p-6 flex flex-col justify-between hover:shadow-md transition">
            <div>
                <div class="flex justify-between items-start gap-4 mb-3">
                    <h3 class="text-xl font-semibold text-emerald-900">{s.name}</h3>
                    <span class="text-lg font-bold text-amber-700">${s.price:.2f}</span>
                </div>
                <p class="text-stone-600 text-sm mb-4 leading-relaxed">{s.description}</p>
            </div>
            <div class="border-t border-stone-100 pt-4 flex justify-between items-center text-xs text-stone-500">
                <span>⏱️ {s.duration} mins</span>
                <a href="/book?service_id={s.id}" class="bg-emerald-800 text-white px-4 py-2 rounded-xl hover:bg-emerald-700 font-semibold transition">
                    Reservar
                </a>
            </div>
        </div>
        """

    content = f"""
    {HTML_HEADER}
    <main class="max-w-6xl mx-auto px-6 py-10">
        <div class="text-center max-w-2xl mx-auto mb-12">
            <h1 class="text-4xl font-bold text-emerald-950 mb-4">Experiencias de Bienestar</h1>
            <p class="text-stone-600">Explora nuestro menú de tratamientos premium diseñados para tu relajación y cuidado de la piel.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            {catalog_cards}
        </div>
    </main>
    {HTML_FOOTER}
    """
    return content

@app.get("/book", response_class=HTMLResponse)
def book_form(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return RedirectResponse(url="/")
        
    content = f"""
    {HTML_HEADER}
    <main class="max-w-xl mx-auto px-6 py-12">
        <div class="bg-white rounded-2xl shadow-md border border-emerald-100 p-8">
            <h2 class="text-3xl font-bold text-emerald-950 mb-2">Reservar Turno</h2>
            <p class="text-amber-700 font-medium mb-6">Servicio elegido: {service.name}</p>
            
            <form action="/book" method="post" class="space-y-4">
                <input type="hidden" name="service_id" value="{service.id}">
                <div>
                    <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Nombre del Cliente</label>
                    <input type="text" name="client_name" required class="w-full border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-600">
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Teléfono</label>
                        <input type="tel" name="client_phone" required class="w-full border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-600">
                    </div>
                    <div>
                        <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Email</label>
                        <input type="email" name="client_email" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-600">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Fecha y Hora</label>
                    <input type="datetime-local" name="appointment_time" required class="w-full border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-600">
                </div>
                <div>
                    <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Notas / Tipo de Piel</label>
                    <textarea name="client_notes" rows="3" placeholder="Ej: Piel grasa, alergia a algún componente..." class="w-full border border-stone-200 rounded-xl px-4 py-2.5 focus:outline-none focus:border-emerald-600 text-sm"></textarea>
                </div>
                <button type="submit" class="w-full bg-emerald-900 text-white font-semibold py-3 rounded-xl hover:bg-emerald-800 transition">
                    Agendar Servicio
                </button>
            </form>
        </div>
    </main>
    {HTML_FOOTER}
    """
    return content

@app.post("/book")
def save_booking(
    service_id: int = Form(...),
    client_name: str = Form(...),
    client_phone: str = Form(...),
    client_email: str = Form(None),
    appointment_time: str = Form(...),
    client_notes: str = Form(None),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.phone == client_phone).first()
    if not client:
        client = Client(name=client_name, phone=client_phone, email=client_email, notes=client_notes)
        db.add(client)
        db.commit()
        db.refresh(client)
    
    appointment = Appointment(client_id=client.id, service_id=service_id, date_time=appointment_time)
    db.add(appointment)
    db.commit()
    
    return RedirectResponse(url="/appointments", status_code=303)

@app.get("/appointments", response_class=HTMLResponse)
def list_appointments(db: Session = Depends(get_db)):
    appointments = db.query(Appointment).all()
    table_rows = ""
    if not appointments:
        table_rows = "<tr><td colspan='5' class='px-6 py-10 text-center text-stone-500'>No hay citas registradas aún.</td></tr>"
    else:
        for appt in appointments:
            formatted_date = appt.date_time.replace("T", " ")
            table_rows += f"""
            <tr class="border-b border-stone-100 hover:bg-stone-50/50 transition">
                <td class="px-6 py-4 font-semibold text-emerald-950">{appt.client.name}</td>
                <td class="px-6 py-4 text-sm text-stone-600">{appt.client.phone}</td>
                <td class="px-6 py-4 font-medium text-amber-800">{appt.service.name}</td>
                <td class="px-6 py-4 text-sm text-stone-600">{formatted_date}</td>
                <td class="px-6 py-4 text-xs"><span class="px-2.5 py-1 rounded-full bg-yellow-100 text-yellow-800 font-semibold">{appt.status}</span></td>
            </tr>
            """
            
    content = f"""
    {HTML_HEADER}
    <main class="max-w-6xl mx-auto px-6 py-10">
        <h2 class="text-3xl font-bold text-emerald-950 mb-6">Agenda de Turnos</h2>
        <div class="bg-white rounded-2xl shadow-sm border border-emerald-100 overflow-hidden">
            <table class="w-full border-collapse text-left">
                <thead class="bg-emerald-900/5 text-emerald-950 uppercase text-xs font-bold tracking-wider">
                    <tr>
                        <th class="px-6 py-4">Cliente</th>
                        <th class="px-6 py-4">Teléfono</th>
                        <th class="px-6 py-4">Tratamiento</th>
                        <th class="px-6 py-4">Fecha y Hora</th>
                        <th class="px-6 py-4">Estado</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-stone-100">{table_rows}</tbody>
            </table>
        </div>
    </main>
    {HTML_FOOTER}
    """
    return content

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    