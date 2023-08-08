from werkzeug.utils import secure_filename
name = "my file.txt"
secure_name = secure_filename(name)
print(f"Before :{name}")
print(f"After : {secure_name}")