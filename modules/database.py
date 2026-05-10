import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def cargar_planes():
    supabase = get_supabase()
    ase = supabase.table("aseguradoras").select("id, nombre").execute()
    ase_dict = {a["id"]: a["nombre"] for a in ase.data}
    planes = supabase.table("planes").select("id, nombre, aseguradora_id").execute()
    return {f"{ase_dict[p['aseguradora_id']]} - {p['nombre']}": p["id"] for p in planes.data}

def buscar_copago_y_hospitales(especialidad, plan_id):
    supabase = get_supabase()
    try:
        esp = supabase.table("especialidades").select("id").eq("nombre", especialidad).execute()
        if not esp.data:
            return None, []
        esp_id = esp.data[0]["id"]
        copago_res = supabase.table("copagos").select("valor_copago").eq("plan_id", plan_id).eq("especialidad_id", esp_id).execute()
        copago = copago_res.data[0]["valor_copago"] if copago_res.data else None
        red_res = supabase.table("redes_hospitales").select("hospital_id").eq("plan_id", plan_id).execute()
        hospital_ids = [h["hospital_id"] for h in red_res.data] if red_res.data else []
        if hospital_ids:
            hosp_res = supabase.table("hospitales").select("nombre, ciudad, costo_consulta_base").in_("id", hospital_ids).execute()
            hospitales = hosp_res.data if hosp_res.data else []
            hospitales.sort(key=lambda x: x["costo_consulta_base"])
            return copago, hospitales
        return copago, []
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return None, []