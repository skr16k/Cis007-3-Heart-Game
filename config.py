import os
SECRET_KEY=os.environ.get('SECRET_KEY','dev-secret')
DB_PATH=os.environ.get('DB_PATH',os.path.join(os.path.dirname(__file__),'data','app.db'))
HEART_API_ENDPOINTS=['https://marcconrad.com/uob/heart/api.php','https://marcconrad.com/uob/heart/compute.php']
