def number_to_words_es(number):
    """
    Convierte un número a palabras en español (formato para moneda peruana)
    """
    unidades = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
    decenas = ["", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
    especiales = {11: "ONCE", 12: "DOCE", 13: "TRECE", 14: "CATORCE", 15: "QUINCE", 
                  16: "DIECISEIS", 17: "DIECISIETE", 18: "DIECIOCHO", 19: "DIECINUEVE",
                  21: "VEINTIUNO", 22: "VEINTIDOS", 23: "VEINTITRES", 24: "VEINTICUATRO",
                  25: "VEINTICINCO", 26: "VEINTISEIS", 27: "VEINTISIETE", 28: "VEINTIOCHO", 29: "VEINTINUEVE"}
    centenas = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", 
                "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]

    def convert_block(n):
        if n == 0: return ""
        if n == 100: return "CIEN"
        
        c = n // 100
        d = (n % 100) // 10
        u = n % 10
        
        res = centenas[c]
        
        if n % 100 > 0:
            if res: res += " "
            if 10 < n % 100 < 30 and (n % 100) in especiales:
                res += especiales[n % 100]
            else:
                if d > 0:
                    res += decenas[d]
                    if u > 0:
                        res += " Y " + unidades[u]
                elif u > 0:
                    res += unidades[u]
        return res

    def convert_full(n):
        if n == 0: return "CERO"
        
        miles = n // 1000
        resto = n % 1000
        
        res = ""
        if miles > 0:
            if miles == 1:
                res = "MIL"
            else:
                res = convert_block(miles) + " MIL"
        
        if resto > 0:
            if res: res += " "
            res += convert_block(resto)
            
        return res

    # Separar enteros y decimales
    entero = int(number)
    decimal = int(round((number - entero) * 100))
    
    palabras = convert_full(entero)
    # Ajuste para "UN" -> "UNO" no es necesario en este contexto de moneda
    
    return f"{palabras} CON {decimal:02d}/100 SOLES"

def extraer_skus_base(sku_woo):
    """
    Extrae todos los segmentos numéricos de 7 u 8 dígitos del SKU.
    Ignora sufijos no numéricos y números cortos (como variaciones locales).
    Ej: "1003226-1007031-S1046" -> ["1003226", "1007031"]
    """
    import re
    if not sku_woo:
        return []
    
    # Dividir por guiones
    partes = str(sku_woo).split('-')
    
    # Filtrar solo partes que sean exactamente 7 u 8 dígitos numéricos
    # (El POS usa 7 dígitos 100XXXX, pero pronto llegará a 10XXXXXX)
    skus_extraidos = [p for p in partes if re.fullmatch(r'\d{7,8}', p)]
    
    return skus_extraidos
