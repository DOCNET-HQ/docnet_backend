import os
import requests
from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings
import tempfile
from profiles.models import Specialty


class Command(BaseCommand):
    help = "Download and assign images to specialties from the provided URLs"

    def handle(self, *args, **options):
        specialties_data = [
            {
                "name": "Cardiology",
                "img": "https://www.mayoclinic.org/-/media/kcms/gbs/medical-professionals/images/2025/03/14/20/27/cardio-advances-767x535.jpg",
            },
            {
                "name": "Neurology",
                "img": "https://www.cnos.net/wp-content/uploads/2022/12/Neurology.jpg",
            },
            {
                "name": "Pediatrics",
                "img": "https://commonwealthpeds.com/wp-content/uploads/2025/03/ComPed-What-Does-a-Pediatrician-Do-Blog.png",
            },
            {
                "name": "Orthopedics",
                "img": "https://irp.cdn-website.com/b174dce8/dms3rep/multi/bb-a94f4f13.PNG",
            },
            {
                "name": "Dermatology",
                "img": "https://plymouthmeetingdermatology.com/wp-content/uploads/2021/12/plym_in_office.jpg",
            },
            {
                "name": "Psychiatry",
                "img": "https://mb.futurepsychsolutions.com/wp-content/uploads/psychiatrist-2302.jpg",
            },
            {
                "name": "Radiology",
                "img": "https://www.cambridgehealth.edu/wp-content/uploads/2021/09/radiation.jpg",
            },
            {
                "name": "General",
                "img": "https://img.lb.wbmdstatic.com/vim/live/webmd/consumer_assets/site_images/article_thumbnails/BigBead/general_practitioners_what_to_know_bigbead/1800x1200_general_practitioners_what_to_know_bigbead.jpg",
            },
            {
                "name": "Gynecology",
                "img": "https://grandpeaks.org/wp-content/uploads/female-gynecologist-doing-ultrasound-examination-o-2024-10-22-06-13-36-utc-1.jpg",
            },
            {
                "name": "Oncology",
                "img": "https://www.excelsior.edu/wp-content/uploads/2022/07/oncology-nursing.jpg",
            },
            {
                "name": "Urogynecology",
                "img": "https://www.uabmedicine.org/wp-content/uploads/sites/3/2025/02/What-is-a-urogynecologist.png",
            },
            {
                "name": "Mastology",
                "img": "https://iqinterquirofanos.com/wp-content/uploads/2024/12/mastologia.jpg",
            },
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        for specialty_data in specialties_data:
            name = specialty_data["name"]
            img_url = specialty_data["img"]

            try:
                # Find the specialty by name
                specialty = Specialty.objects.get(name=name)
                self.stdout.write(f"Processing {name}...")

                # Skip if image already exists
                if specialty.image and specialty.image.name:
                    self.stdout.write(f"  Image already exists for {name}, skipping...")
                    continue

                # Download the image
                response = requests.get(img_url, headers=headers, timeout=30)
                response.raise_for_status()

                # Get file extension from URL
                file_extension = os.path.splitext(img_url.split("/")[-1])[1]
                if not file_extension:
                    file_extension = ".jpg"  # default extension

                # Create a temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_extension
                ) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file.flush()

                    # Save to the specialty's image field
                    filename = f"{name.lower().replace(' ', '_')}{file_extension}"
                    with open(tmp_file.name, "rb") as f:
                        specialty.image.save(filename, File(f), save=True)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Successfully downloaded and assigned image for {name}"
                    )
                )

            except Specialty.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"  Specialty '{name}' not found in database")
                )
            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f"  Failed to download image for {name}: {str(e)}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Unexpected error for {name}: {str(e)}")
                )

        self.stdout.write(self.style.SUCCESS("Finished processing all specialties"))
