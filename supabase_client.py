import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xoizmtkayynkwrpgyxgz.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_HTBQcUfRLs5dlKy-9RoEbA_EJgvRf5R")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
