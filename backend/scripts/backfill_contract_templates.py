import os
import sys
from dotenv import load_dotenv

# Load environment variables first
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print("Warning: .env file not found. Make sure your environment variables are set.")

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, ContractTemplate

def backfill_contract_templates():
    """
    Ensures all users have a default contract template.
    """
    app = create_app()
    with app.app_context():
        print("Starting backfill process for default contract templates...")
        
        try:
            all_users = User.query.all()
            if not all_users:
                print("No users found.")
                return

            print(f"Found {len(all_users)} users. Checking for default contract template...")

            contract_content = """Entre les soussignés :
Realestate Factory SARLauRC:21658ICE: 0037189980000096
       (Agence de Gestion)
Représentée par
Nom: Hamza HAKIM 
CIN : BK388641
Dénommé le bailleur d’une part
Et :
Nom : {{guest_name}} CIN/PASSPORT : {{guest_cin}}
Prénom : {{guest_firstname}}
Adresse : {{guest_address}}
Tél : {{guest_phone}}
Dénommé le locataire d’autre part

Il a été convenu d’une location saisonnière d’un appartement meublé qui se compose de deux niveaux et reparti comme suit:
   Un salon, Un WC, Une cuisine, Une terrasse,  Une chambre avec une salle de bain et douche

    • Adresse Rue Ahmed Amine, Imm Vertu, N7, 1er Etage - Appartement n°: {{property_apartment_number}}

    • Période de la location : du {{check_in_date}} au {{check_out_date}}  ({{number_of_nights}} nuitées).

    • Montant du loyer : {{rent_per_night}} dhs/nuit, soit la somme de {{total_rent}} dhs.

Obligations du locataire :

    • Le locataire s’engage à régler la totalité du montant de la location au moment de la signature du présent contrat. Aucun remboursement ne pourra être exigé en cas de départ anticipé, quel qu’en soit le motif.
    • Le locataire s’engage à occuper les lieux personnellement, à les utiliser “en bon père de famille” et à les entretenir avec soin pendant toute la durée de la location.
    • Ne pas dépasser le nombre maximum de personnes autorisés à séjourner (Max 3 pers).
    • Toutes les installations sont en état de marche et toute réclamation les concernant survenant plus de 3 jours après l’entrée en jouissance des lieux, ne pourra être admise. Les réparations rendues nécessaires par la négligence ou le mauvais entretien en cours de location, seront à la charge du locataire.
    • Le locataire s’engage à respecter la tranquillité des lieux et à ne pas troubler le voisinage, que ce soit par lui-même ou par ses accompagnants.
    • Rendre l’appartement propre et en bon état lors du départ. (L’heure du départ est fixée à 11h00 au plus tard).

Le non respects des obligations par le locataire donne lieu à la résiliation de ce contrat voir même à des poursuites en dommages et intérêts.
Fait en deux exemplaires à Casablanca . Le {{contract_date}}
Le bailleurLe locataire
"""
            
            templates_created_count = 0
            for user in all_users:
                # Check if a default contract template already exists for this user
                existing_template = ContractTemplate.query.filter_by(
                    user_id=user.id,
                    is_default=True
                ).first()

                if not existing_template:
                    templates_created_count += 1
                    print(f"  -> User '{user.name}' is missing a default contract template. Creating one...")
                    
                    default_contract = ContractTemplate(
                        user_id=user.id,
                        name="Default Seasonal Rental Agreement",
                        template_content=contract_content,
                        language="fr",
                        is_default=True
                    )
                    db.session.add(default_contract)

            if templates_created_count > 0:
                db.session.commit()
                print(f"\nSuccessfully created default contract templates for {templates_created_count} users.")
            else:
                print("\nAll users already have a default contract template. No action was needed.")

            print("Backfill process complete.")

        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction has been rolled back.")

if __name__ == "__main__":
    backfill_contract_templates()
