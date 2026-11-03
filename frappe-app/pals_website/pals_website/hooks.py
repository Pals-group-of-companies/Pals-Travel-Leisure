app_name = "pals_website"
app_title = "Pals Website"
app_publisher = "Pals Group of Companies"
app_description = "Login, data and booking requests for the Pals Travel & Leisure website"
app_email = "info@palstravelleisure.co.ke"
app_license = "MIT"

after_install = "pals_website.setup.ensure_role"
after_migrate = "pals_website.setup.ensure_role"
