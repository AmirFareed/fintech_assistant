"""
Run this script ONCE to populate the services table for all departments.
Usage: python setup_services.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def get_department_id(slug: str) -> str | None:
    res = supabase.table("departments").select("id").eq("slug", slug).single().execute()
    return res.data["id"] if res.data else None


SERVICES = [
    # ── Housing Department ────────────────────────────────────────────────────
    {
        "dept_slug": "housing-department",
        "service_name": "Government Employee Housing Scheme",
        "service_slug": "housing-employee-scheme",
        "summary": "Apply for affordable residential plots under the KP government employee housing scheme.",
        "official_link": "https://housing.kp.gov.pk/",
        "fee_link": "https://housing.kp.gov.pk/",
        "keywords": ["housing", "plot", "scheme", "government employee", "house", "allotment", "ballot", "residential"],
        "is_active": True,
    },
    {
        "dept_slug": "housing-department",
        "service_name": "Housing Scheme Plot Status Check",
        "service_slug": "housing-plot-status",
        "summary": "Check the status of your housing scheme application and ballot result.",
        "official_link": "https://housing.kp.gov.pk/",
        "fee_link": None,
        "keywords": ["plot status", "housing status", "ballot result", "application status", "allocation"],
        "is_active": True,
    },
    {
        "dept_slug": "housing-department",
        "service_name": "Housing Scheme Document Submission",
        "service_slug": "housing-document-submission",
        "summary": "Submit additional documents requested by the Housing Department for your application.",
        "official_link": "https://housing.kp.gov.pk/",
        "fee_link": None,
        "keywords": ["document submission", "housing documents", "upload documents", "housing application"],
        "is_active": True,
    },

    # ── Transport Department ──────────────────────────────────────────────────
    {
        "dept_slug": "transport-department",
        "service_name": "New Vehicle Registration",
        "service_slug": "transport-new-vehicle-registration",
        "summary": "Register a newly purchased vehicle in KP through the Dastak app.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://www.kpexcise.gov.pk/app/motor-vehicle-taxes/",
        "keywords": ["vehicle registration", "new car", "register vehicle", "number plate", "token tax", "register car", "new motorcycle"],
        "is_active": True,
    },
    {
        "dept_slug": "transport-department",
        "service_name": "Vehicle Transfer of Ownership",
        "service_slug": "transport-vehicle-transfer",
        "summary": "Transfer vehicle ownership from seller to buyer digitally through Dastak.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://www.kpexcise.gov.pk/app/motor-vehicle-taxes/",
        "keywords": ["vehicle transfer", "ownership transfer", "sell car", "buy car", "transfer car", "vehicle ownership change"],
        "is_active": True,
    },
    {
        "dept_slug": "transport-department",
        "service_name": "Learner Driving License",
        "service_slug": "transport-learner-license",
        "summary": "Apply for a learner driving permit for LTV, HTV, motorcycle, tractor, or rickshaw.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://transport.kp.gov.pk/",
        "keywords": ["learner license", "learner permit", "learning license", "L plate", "driving permit", "first license", "new license"],
        "is_active": True,
    },
    {
        "dept_slug": "transport-department",
        "service_name": "Permanent Driving License Renewal",
        "service_slug": "transport-license-renewal",
        "summary": "Renew an expired or expiring permanent driving license in KP.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://transport.kp.gov.pk/",
        "keywords": ["license renewal", "renew driving license", "expired license", "driving license renew"],
        "is_active": True,
    },

    # ── Excise (Motor Vehicle) ────────────────────────────────────────────────
    {
        "dept_slug": "excise-motor-vehicle",
        "service_name": "Motor Vehicle Registration Tax",
        "service_slug": "excise-vehicle-registration-tax",
        "summary": "Calculate and pay registration tax and lifetime token tax for new vehicles in KP.",
        "official_link": "https://www.kpexcise.gov.pk/",
        "fee_link": "https://www.kpexcise.gov.pk/app/motor-vehicle-taxes/",
        "keywords": ["registration tax", "vehicle tax", "motor vehicle tax", "token tax", "advance tax", "excise", "registration fee"],
        "is_active": True,
    },
    {
        "dept_slug": "excise-motor-vehicle",
        "service_name": "Token Tax Payment",
        "service_slug": "excise-token-tax-payment",
        "summary": "Pay annual token tax for your registered vehicle in Khyber Pakhtunkhwa.",
        "official_link": "https://www.kpexcise.gov.pk/",
        "fee_link": "https://www.kpexcise.gov.pk/app/motor-vehicle-taxes/",
        "keywords": ["token tax", "annual tax", "vehicle tax payment", "road tax", "excise tax"],
        "is_active": True,
    },
    {
        "dept_slug": "excise-motor-vehicle",
        "service_name": "Vehicle Fitness Certificate",
        "service_slug": "excise-fitness-certificate",
        "summary": "Obtain a vehicle fitness certificate for commercial vehicles confirming roadworthiness.",
        "official_link": "https://www.kpexcise.gov.pk/",
        "fee_link": "https://www.kpexcise.gov.pk/",
        "keywords": ["fitness certificate", "vehicle fitness", "roadworthy", "commercial vehicle", "bus fitness", "truck fitness"],
        "is_active": True,
    },

    # ── Property Tax (Urban Immovable) ────────────────────────────────────────
    {
        "dept_slug": "property-tax-urban-immovable",
        "service_name": "Property Tax Assessment",
        "service_slug": "property-tax-assessment",
        "summary": "Get your urban property assessed for Urban Immovable Property Tax (UIPT) in KP.",
        "official_link": "https://excise_taxation.kp.gov.pk/page/urban_immovable_property_tax",
        "fee_link": "https://www.kpexcise.gov.pk/app/uiptaxcomarea/",
        "keywords": ["property tax", "UIPT", "urban property", "property assessment", "annual rental value", "ARV", "house tax"],
        "is_active": True,
    },
    {
        "dept_slug": "property-tax-urban-immovable",
        "service_name": "Property Tax Payment",
        "service_slug": "property-tax-payment",
        "summary": "Pay your assessed urban immovable property tax online through Dastak.",
        "official_link": "https://excise_taxation.kp.gov.pk/page/urban_immovable_property_tax",
        "fee_link": "https://www.kpexcise.gov.pk/app/uiptaxcomarea/",
        "keywords": ["property tax payment", "pay house tax", "UIPT payment", "property tax due", "property tax arrears"],
        "is_active": True,
    },
    {
        "dept_slug": "property-tax-urban-immovable",
        "service_name": "Property Tax Exemption Application",
        "service_slug": "property-tax-exemption",
        "summary": "Apply for property tax exemption for eligible residential, religious, or charitable properties.",
        "official_link": "https://excise_taxation.kp.gov.pk/page/urban_immovable_property_tax",
        "fee_link": "https://www.kpexcise.gov.pk/app/uiptaxcomarea/",
        "keywords": ["property tax exemption", "tax exempt property", "mosque tax", "property exemption", "small property exempt"],
        "is_active": True,
    },

    # ── KP Traffic Police ─────────────────────────────────────────────────────
    {
        "dept_slug": "kp-traffic-police",
        "service_name": "Learner Permit",
        "service_slug": "traffic-learner-permit",
        "summary": "Apply for a learner driving permit through KP Traffic Police via the Dastak app.",
        "official_link": "https://ptpkp.gov.pk/",
        "fee_link": "https://ptpkp.gov.pk/",
        "keywords": ["learner permit", "L plate", "learning to drive", "learner driving", "first driving permit", "beginner driver"],
        "is_active": True,
    },
    {
        "dept_slug": "kp-traffic-police",
        "service_name": "Permanent Driving License",
        "service_slug": "traffic-permanent-license",
        "summary": "Obtain a permanent RFID-based driving license after passing the KP Traffic Police test.",
        "official_link": "https://ptpkp.gov.pk/",
        "fee_link": "https://ptpkp.gov.pk/",
        "keywords": ["permanent license", "driving license", "RFID license", "driving test", "license card", "traffic police license"],
        "is_active": True,
    },
    {
        "dept_slug": "kp-traffic-police",
        "service_name": "Driving License Verification",
        "service_slug": "traffic-license-verification",
        "summary": "Verify the authenticity and status of any KP-issued driving license online using CNIC.",
        "official_link": "https://ptpkp.gov.pk/driving-license-verification/",
        "fee_link": None,
        "keywords": ["license verification", "check license", "verify driving license", "license status", "license check"],
        "is_active": True,
    },
    {
        "dept_slug": "kp-traffic-police",
        "service_name": "Driving License Renewal",
        "service_slug": "traffic-license-renewal",
        "summary": "Renew an expired or expiring KP driving license through the Dastak app.",
        "official_link": "https://ptpkp.gov.pk/",
        "fee_link": "https://ptpkp.gov.pk/",
        "keywords": ["renew license", "license renewal", "expired driving license", "traffic police renewal"],
        "is_active": True,
    },

    # ── Agriculture Income Tax ────────────────────────────────────────────────
    {
        "dept_slug": "agriculture-income-tax",
        "service_name": "Agriculture Income Tax Registration",
        "service_slug": "agri-tax-registration",
        "summary": "Register for Agriculture Income Tax in KP if your annual farm income exceeds Rs. 600,000.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://revenue.kp.gov.pk/",
        "keywords": ["agriculture tax", "farm tax", "agriculture income", "farming tax", "kisaan tax", "agricultural registration"],
        "is_active": True,
    },
    {
        "dept_slug": "agriculture-income-tax",
        "service_name": "Agriculture Income Tax Filing",
        "service_slug": "agri-tax-filing",
        "summary": "File your annual Agriculture Income Tax return in Khyber Pakhtunkhwa.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://revenue.kp.gov.pk/",
        "keywords": ["agriculture tax return", "farm tax filing", "agri income return", "file agriculture tax", "annual tax return"],
        "is_active": True,
    },
    {
        "dept_slug": "agriculture-income-tax",
        "service_name": "Agriculture Tax Exemption Certificate",
        "service_slug": "agri-tax-exemption",
        "summary": "Obtain an exemption certificate for farmers with annual income below Rs. 600,000.",
        "official_link": "https://dastak.kp.gov.pk/",
        "fee_link": "https://revenue.kp.gov.pk/",
        "keywords": ["agriculture exemption", "farm tax exempt", "kisaan exemption", "small farmer", "agriculture certificate"],
        "is_active": True,
    },

    # ── Arms & Ammunition License (Dealership/Manufacturing) ──────────────────
    {
        "dept_slug": "arms-ammunition-license",
        "service_name": "Arms Dealership License",
        "service_slug": "arms-ammo-dealership",
        "summary": "Apply for a license to operate an arms dealership shop in Khyber Pakhtunkhwa.",
        "official_link": "https://hd.kp.gov.pk/",
        "fee_link": "https://dastak.kp.gov.pk/",
        "keywords": ["arms dealer", "dealership license", "gun shop", "firearms dealer", "ammunition dealer", "arms shop"],
        "is_active": True,
    },
    {
        "dept_slug": "arms-ammunition-license",
        "service_name": "Arms Manufacturing License",
        "service_slug": "arms-ammo-manufacturing",
        "summary": "Apply for a license to manufacture firearms or ammunition in KP.",
        "official_link": "https://hd.kp.gov.pk/",
        "fee_link": "https://hd.kp.gov.pk/",
        "keywords": ["arms manufacturing", "gun factory", "gunsmith license", "firearms manufacturing", "Darra Adam Khel", "weapon making"],
        "is_active": True,
    },
    {
        "dept_slug": "arms-ammunition-license",
        "service_name": "Arms Repair Workshop License",
        "service_slug": "arms-ammo-repair",
        "summary": "Obtain a license to operate an arms repair and maintenance workshop in KP.",
        "official_link": "https://hd.kp.gov.pk/",
        "fee_link": "https://dastak.kp.gov.pk/",
        "keywords": ["arms repair", "gun repair", "weapon repair", "gunsmith", "repair workshop", "firearm maintenance"],
        "is_active": True,
    },
]


def main():
    print("Setting up services in Supabase...\n")

    inserted = 0
    skipped = 0
    errors = 0

    for svc in SERVICES:
        dept_id = get_department_id(svc["dept_slug"])
        if not dept_id:
            print(f"  [SKIP] Department not found: {svc['dept_slug']}")
            skipped += 1
            continue

        # Check if service already exists
        existing = (
            supabase.table("services")
            .select("id")
            .eq("service_slug", svc["service_slug"])
            .execute()
        )
        if existing.data:
            print(f"  [EXISTS] {svc['service_name']}")
            skipped += 1
            continue

        try:
            supabase.table("services").insert({
                "department_id": dept_id,
                "service_name": svc["service_name"],
                "service_slug": svc["service_slug"],
                "summary": svc["summary"],
                "official_link": svc.get("official_link"),
                "fee_link": svc.get("fee_link"),
                "keywords": svc.get("keywords", []),
                "is_active": svc.get("is_active", True),
            }).execute()
            print(f"  [OK] Inserted: {svc['service_name']}")
            inserted += 1
        except Exception as e:
            print(f"  [ERROR] {svc['service_name']}: {e}")
            errors += 1

    print(f"\nDone. Inserted: {inserted} | Skipped/Exists: {skipped} | Errors: {errors}")


if __name__ == "__main__":
    main()
