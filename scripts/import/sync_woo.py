import os
import sys
from woocommerce import API
from app import app, db
from models import Categoria, Producto, Variacion
from dotenv import load_dotenv

load_dotenv()

# Configuración Woo
wcapi = API(
    url=os.getenv("WOO_URL"),
    consumer_key=os.getenv("WOO_CONSUMER_KEY"),
    consumer_secret=os.getenv("WOO_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=30
)

def sync_categories():
    print("🔄 Sincronizando categorías (Paso 1: Creación)...")
    page = 1
    all_cat_data = []
    
    while True:
        params = {"page": page, "per_page": 100}
        response = wcapi.get("products/categories", params=params)
        
        if response.status_code != 200:
            print(f"❌ Error al obtener categorías: {response.text}")
            break
            
        categories = response.json()
        if not categories:
            break
            
        all_cat_data.extend(categories)
        
        for cat_data in categories:
            cat = db.session.get(Categoria, cat_data['id'])
            if not cat:
                cat = Categoria(id=cat_data['id'])
                db.session.add(cat)
            
            cat.nombre = cat_data['name']
            cat.slug = cat_data['slug']
            cat.count = cat_data['count']
            # No pondremos el padre aún para evitar errores de FK
            
        db.session.commit()
        page += 1

    print("🔄 Sincronizando categorías (Paso 2: Relaciones)...")
    for cat_data in all_cat_data:
        if cat_data['parent'] != 0:
            cat = db.session.get(Categoria, cat_data['id'])
            # Verificar que el padre existe
            if db.session.get(Categoria, cat_data['parent']):
                cat.padre_id = cat_data['parent']
            
    db.session.commit()
    print(f"✅ {len(all_cat_data)} categorías sincronizadas.")

def sync_products():
    print("🔄 Sincronizando productos...")
    page = 1
    total_synced = 0
    
    while True:
        params = {"page": page, "per_page": 50, "status": "publish"} # Reducido para evitar timeouts
        response = wcapi.get("products", params=params)
        
        if response.status_code != 200:
            print(f"❌ Error al obtener productos: {response.text}")
            break
            
        products = response.json()
        if not products:
            break
            
        for p_data in products:
            prod = db.session.get(Producto, p_data['id'])
            if not prod:
                prod = Producto(id=p_data['id'])
                db.session.add(prod)
            
            prod.nombre = p_data['name']
            prod.sku = p_data['sku']
            prod.precio = p_data['price'] if p_data['price'] else 0.00
            prod.stock_status = p_data['stock_status']
            prod.tipo = p_data['type']
            
            # Categoria principal y todas las relaciones
            if p_data['categories']:
                prod.categoria_id = p_data['categories'][0]['id']
                cat_ids = [c['id'] for c in p_data['categories']]
                prod.categorias = [] 
                for cid in cat_ids:
                    cat_obj = db.session.get(Categoria, cid)
                    if cat_obj:
                        prod.categorias.append(cat_obj)
            
            # Imagen (la primera)
            if p_data['images']:
                prod.imagen_url = p_data['images'][0]['src']
            
            # Sincronizar variaciones si es variable
            if prod.tipo == 'variable':
                sync_product_variations(prod.id)
                
            total_synced += 1
            
        db.session.commit()
        print(f"   Procesados {total_synced} productos...")
        page += 1
        
    print(f"✅ {total_synced} productos sincronizados.")

def sync_product_variations(product_id):
    """Sincroniza todas las variaciones de un producto"""
    print(f"      ∟ Sincronizando variaciones del producto {product_id}...")
    response = wcapi.get(f"products/{product_id}/variations", params={"per_page": 100})
    
    if response.status_code != 200:
        print(f"      ⚠️ Error variaciones {product_id}: {response.text}")
        return

    variations = response.json()
    for v_data in variations:
        v_id = v_data['id']
        var = db.session.get(Variacion, v_id)
        if not var:
            var = Variacion(id=v_id, producto_id=product_id)
            db.session.add(var)
        
        var.sku = v_data['sku']
        var.precio = v_data['price'] if v_data['price'] else 0.00
        var.stock_status = v_data['stock_status']
        var.atributos = {a['name']: a['option'] for a in v_data['attributes']}
        
        if v_data['image']:
            var.imagen_url = v_data['image']['src']

if __name__ == "__main__":
    with app.app_context():
        try:
            sync_categories()
            sync_products()
            print("\n🎉 Sincronización completada con éxito.")
        except Exception as e:
            print(f"\n❌ Error crítico durante la sincronización: {str(e)}")
            db.session.rollback()
