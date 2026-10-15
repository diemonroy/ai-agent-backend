#!/usr/bin/env python3
"""
CLI de Inspección y Diagnóstico de Base de Datos Relacional
Diego Monroy — Executive AI Talent Agent

Permite consultar el estado, tablas, sesiones, mensajes y conversiones
directamente desde la terminal con formato visual limpio.

Uso:
    python inspect_db.py                # Resumen general y estado de la base de datos
    python inspect_db.py --sessions     # Lista todas las sesiones con contexto de reclutador
    python inspect_db.py --messages <id># Muestra los mensajes de una sesión específica
    python inspect_db.py --backup       # Genera una copia de seguridad en caliente
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Añadir raíz al sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import db_manager


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def show_summary():
    status = db_manager.get_database_status()
    print_banner("📊 ESTADO Y CONFIGURACIÓN DE BASE DE DATOS")
    print(f"  • Estado:            {status['status'].upper()}")
    print(f"  • Motor:             {status['engine'].upper()} (Relacional)")
    print(f"  • Archivo Físico:    {status['databasePath']}")
    print(f"  • Tamaño en Disco:   {status['sizeFormatted']} ({status['sizeBytes']:,} bytes)")
    print(f"  • Modo de Journal:   {status['journalMode']} (Alta Concurrencia)")
    print(f"  • Verificado en:     {status['verifiedAt']}")
    print("-" * 70)
    print("  📋 CONTEO DE REGISTROS POR TABLA:")
    for table, count in status["tables"].items():
        print(f"    - {table:<20} {count:>6} filas")
    print("-" * 70)
    print("  🎯 MÉTRICAS DE CONVERSIÓN & LEAD DISCOVERY:")
    print(f"    - Entrevistas Presenciales (Bogotá): {status['metrics']['presencialInterviews']}")
    print(f"    - Entrevistas Virtuales (Meet):      {status['metrics']['virtualInterviews']}")
    print(f"    - Clics de Cierre (Calendar/WA):     {status['metrics']['totalConversions']}")

    if status["recentSessions"]:
        print_banner("🕒 ÚLTIMAS SESIONES REGISTRADAS")
        for s in status["recentSessions"]:
            modality_icon = "📍 Presencial" if s["interviewModality"] == "presencial" else "💻 Virtual"
            print(f"  [{s['updatedAt'][:19]}] ID: {s['sessionId']}")
            print(f"    👤 Reclutador: {s['recruiterName'] or 'No especificado'} | 🏢 Empresa: {s['companyName'] or 'No especificada'}")
            print(f"    💼 Rol: {s['roleDetected'] or 'General'} (Afinidad: {s['matchScore']}%) | {modality_icon}")
            print("  " + "-" * 66)
    print()


def show_sessions():
    print_banner("📋 LISTADO COMPLETO DE SESIONES REGISTRADAS")
    with db_manager.session_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, recruiter_name, company_name, role_detected, match_score,
                   interview_modality, conversion_type, status, updated_at
            FROM sessions ORDER BY updated_at DESC;
        """)
        rows = cursor.fetchall()
        if not rows:
            print("  (No hay sesiones registradas aún)")
            return

        for idx, r in enumerate(rows, start=1):
            modality = "📍 Presencial (Bogotá)" if r["interview_modality"] == "presencial" else "💻 Virtual"
            print(f"  #{idx} | Sesión: {r['session_id']}")
            print(f"     Fecha:       {r['updated_at']}")
            print(f"     Reclutador:  {r['recruiter_name'] or 'Anónimo / Reclutador'}")
            print(f"     Empresa:     {r['company_name'] or 'No detectada'}")
            print(f"     Rol:         {r['role_detected']} ({r['match_score']}% match)")
            print(f"     Modalidad:   {modality}")
            print(f"     Conversión:  {r['conversion_type'] or 'En curso'} | Estado: {r['status']}")
            print("  " + "-" * 66)
    print()


def show_messages(session_id: str):
    print_banner(f"💬 HISTORIAL DE MENSAJES — SESIÓN: {session_id}")
    with db_manager.session_scope() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender, content, attachment_name, timestamp
            FROM messages WHERE session_id = ? ORDER BY timestamp ASC;
        """, (session_id,))
        rows = cursor.fetchall()
        if not rows:
            print(f"  (No se encontraron mensajes para la sesión '{session_id}')")
            return

        for r in rows:
            sender_badge = "👤 RECLUTADOR" if r["sender"] == "user" else "🤖 DIEGO (AGENTE)"
            print(f"\n  [{r['timestamp'][:19]}] {sender_badge}:")
            if r["attachment_name"]:
                print(f"  📎 Adjunto: {r['attachment_name']}")
            print(f"  {r['content']}")
            print("  " + "." * 66)
    print()


def do_backup():
    print_banner("📦 GENERANDO COPIA DE SEGURIDAD")
    backup_file = db_manager.create_backup()
    print(f"  ✅ Backup creado con éxito:")
    print(f"     Ruta:   {backup_file}")
    print(f"     Tamaño: {backup_file.stat().st_size:,} bytes\n")


def main():
    parser = argparse.ArgumentParser(description="Herramienta de diagnóstico de base de datos relacional.")
    parser.add_argument("--sessions", action="store_true", help="Listar todas las sesiones guardadas.")
    parser.add_argument("--messages", type=str, metavar="SESSION_ID", help="Ver mensajes de una sesión.")
    parser.add_argument("--backup", action="store_true", help="Generar un backup relacional.")

    args = parser.parse_args()

    if args.sessions:
        show_sessions()
    elif args.messages:
        show_messages(args.messages)
    elif args.backup:
        do_backup()
    else:
        show_summary()


if __name__ == "__main__":
    main()
