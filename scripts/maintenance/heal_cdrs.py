from app import app, db, Venta
import os

def heal_cdrs():
    with app.app_context():
        ventas = Venta.query.filter(Venta.cdr_path.like('%.zip')).all()
        print(f"Encontradas {len(ventas)} ventas con CDR .zip")
        
        for venta in ventas:
            old_path = venta.cdr_path
            if os.path.exists(old_path):
                new_path = old_path.replace('.zip', '.xml')
                try:
                    os.rename(old_path, new_path)
                    venta.cdr_path = new_path
                    print(f"✅ Sanado: {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                except Exception as e:
                    print(f"❌ Error renombrando {old_path}: {e}")
            else:
                # Si el archivo no existe ficamente, solo actualizamos la ruta para cuando se recupere
                new_path = old_path.replace('.zip', '.xml')
                venta.cdr_path = new_path
                print(f"ℹ Ruta actualizada (archivo no existe): {os.path.basename(new_path)}")
        
        db.session.commit()
        print("Proceso de sanacion completado.")

if __name__ == "__main__":
    heal_cdrs()
