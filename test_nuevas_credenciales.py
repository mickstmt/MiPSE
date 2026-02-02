#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test rápido con nuevas credenciales"""
import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv(override=True)

print("=" * 70)
print("VERIFICACIÓN DE CREDENCIALES")
print("=" * 70)
print(f"RUC: {os.getenv('SUNAT_RUC')}")
print(f"Usuario: {os.getenv('SUNAT_USUARIO_SOL')}")
print(f"Clave: {os.getenv('SUNAT_CLAVE_SOL')}")
print(f"Usuario completo: {os.getenv('SUNAT_RUC')}{os.getenv('SUNAT_USUARIO_SOL')}")
print("=" * 70)
