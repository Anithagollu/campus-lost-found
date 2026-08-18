from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)

from pymongo import MongoClient
from bson import ObjectId

import os
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

app.secret_key = "campus-lost-found-secret-key"

# Image upload settings
UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =====================================================
# DATABASE
# =====================================================

client = MongoClient("mongodb://localhost:27017/")

db = client["CampusLostFound"]

lost_items = db["lost_items"]

found_items = db["found_items"]

users = db["users"]


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    lost_count = lost_items.count_documents({})

    found_count = found_items.count_documents({})

    user_count = users.count_documents({})

    my_lost_count = 0

    my_found_count = 0

    if "user_id" in session:

        user_id = session["user_id"]

        my_lost_count = lost_items.count_documents({
            "user_id": user_id
        })

        my_found_count = found_items.count_documents({
            "user_id": user_id
        })

    return render_template(
        "index.html",

        lost_count=lost_count,

        found_count=found_count,

        user_count=user_count,

        my_lost_count=my_lost_count,

        my_found_count=my_found_count
    )

# =====================================================
# FULL DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")


    # =================================
    # TOTAL COUNTS
    # =================================

    lost_count = lost_items.count_documents({})

    found_count = found_items.count_documents({})

    user_count = users.count_documents({})


    # =================================
    # MY REPORTS
    # =================================

    my_lost_count = lost_items.count_documents({
        "user_id": session["user_id"]
    })

    my_found_count = found_items.count_documents({
        "user_id": session["user_id"]
    })


    # =================================
    # ACTIVE / RESOLVED COUNTS
    # =================================

    active_lost_count = lost_items.count_documents({
        "$or": [
            {"status": "Active"},
            {"status": {"$exists": False}}
        ]
    })

    resolved_lost_count = lost_items.count_documents({
        "status": "Resolved"
    })


    active_found_count = found_items.count_documents({
        "$or": [
            {"status": "Active"},
            {"status": {"$exists": False}}
        ]
    })

    resolved_found_count = found_items.count_documents({
        "status": "Resolved"
    })


    return render_template(
        "dashboard.html",

        lost_count=lost_count,

        found_count=found_count,

        user_count=user_count,

        my_lost_count=my_lost_count,

        my_found_count=my_found_count,

        active_lost_count=active_lost_count,

        resolved_lost_count=resolved_lost_count,

        active_found_count=active_found_count,

        resolved_found_count=resolved_found_count
    )

# =====================================================
# REGISTERED USERS PAGE
# =====================================================

@app.route("/registered-users")
def registered_users():

    if "user_id" not in session:
        return redirect("/login")

    all_users = list(
        users.find(
            {},
            {
                "password": 0
            }
        )
    )

    return render_template(
        "registered_users.html",
        users=all_users
    )

# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        existing_user = users.find_one({
            "email": email
        })

        if existing_user:

            flash(
                "Email already registered!",
                "error"
            )

            return redirect("/register")

        users.insert_one({

            "name": name,

            "email": email,

            "password": password

        })

        flash(
            "Registration successful! Please login.",
            "success"
        )

        return redirect("/login")

    return render_template("register.html")


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        user = users.find_one({

            "email": email,

            "password": password

        })

        if user:

            session["user_id"] = str(
                user["_id"]
            )

            session["user_name"] = user["name"]

            session["user_email"] = user["email"]

            flash(
                "Login successful! Welcome back.",
                "success"
            )

            return redirect("/")

        flash(
            "Invalid email or password!",
            "error"
        )

        return redirect("/login")

    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect("/")


# =====================================================
# REPORT LOST ITEM
# =====================================================

@app.route("/report-lost", methods=["POST"])
def report_lost():

    if "user_id" not in session:

        flash(
            "Please login first!",
            "error"
        )

        return redirect("/login")


    item_name = request.form["item_name"]

    description = request.form["description"]

    location = request.form["location"]

    category = request.form.get(
        "category",
        "Other"
    )

    image_filename = ""


    # IMAGE UPLOAD

    if "image" in request.files:

        image = request.files["image"]

        if image and image.filename:
            print("IMAGE RECEIVED:", image.filename)

            if allowed_file(image.filename):

                filename = secure_filename(
                    image.filename
                )

                # Make filename unique
                import time

                filename = (
                    str(int(time.time()))
                    + "_"
                    + filename
                )

                image.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

                image_filename = filename

            else:

                flash(
                    "Invalid image format!",
                    "error"
                )

                return redirect("/")


    lost_items.insert_one({

        "item_name": item_name,

        "description": description,

        "location": location,

        "category": category,
     
        "image": image_filename,

        "status": "Active",
        
        "reported_at": datetime.now().strftime("%d-%b-%Y, %I:%M %p"),

        "user_id": session["user_id"],

        "user_name": session["user_name"],

        "user_email": session["user_email"]

    })


    flash(
        "Lost item reported successfully!",
        "success"
    )

    return redirect("/")

@app.route("/resolve-lost/<item_id>", methods=["POST"])
def resolve_lost(item_id):

    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect("/login")

    item = lost_items.find_one({
        "_id": ObjectId(item_id)
    })

    if not item:
        flash("Lost item not found!", "error")
        return redirect("/lost-items")

    # Only the person who reported the item can resolve it
    if str(item.get("user_id")) != str(session["user_id"]):
        flash("You can only resolve your own report!", "error")
        return redirect("/lost-items")

    lost_items.update_one(
        {
            "_id": ObjectId(item_id)
        },
        {
            "$set": {
                "status": "Resolved"
            }
        }
    )

    flash(
        "Lost item marked as resolved!",
        "success"
    )

    return redirect("/lost-items")

# =====================================================
# REPORT FOUND ITEM
# =====================================================

@app.route("/report-found", methods=["POST"])
def report_found():

    if "user_id" not in session:

        flash(
            "Please login first!",
            "error"
        )

        return redirect("/login")


    item_name = request.form["item_name"]

    description = request.form["description"]

    location = request.form["location"]

    category = request.form.get(
        "category",
        "Other"
    )

    image_filename = ""


    # IMAGE UPLOAD

    if "image" in request.files:

        image = request.files["image"]

        if image and image.filename:

            if allowed_file(image.filename):

                filename = secure_filename(
                    image.filename
                )

                import time

                filename = (
                    str(int(time.time()))
                    + "_"
                    + filename
                )

                image.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

                image_filename = filename

            else:

                flash(
                    "Invalid image format!",
                    "error"
                )

                return redirect("/")


    found_items.insert_one({

        "item_name": item_name,

        "description": description,

        "location": location,

        "category": category,

        "image": image_filename,

        "status": "Active",
  
        "reported_at": datetime.now().strftime("%d-%b-%Y, %I:%M %p"),

        "user_id": session["user_id"],

        "user_name": session["user_name"],

        "user_email": session["user_email"]

    })


    flash(
        "Found item reported successfully!",
        "success"
    )

    return redirect("/")

@app.route("/resolve-found/<item_id>", methods=["POST"])
def resolve_found(item_id):

    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect("/login")

    item = found_items.find_one({
        "_id": ObjectId(item_id)
    })

    if not item:
        flash("Found item not found!", "error")
        return redirect("/found-items")

    # Only the person who reported the item can resolve it
    if str(item.get("user_id")) != str(session["user_id"]):
        flash("You can only resolve your own report!", "error")
        return redirect("/found-items")

    found_items.update_one(
        {
            "_id": ObjectId(item_id)
        },
        {
            "$set": {
                "status": "Resolved"
            }
        }
    )

    flash(
        "Found item marked as resolved!",
        "success"
    )

    return redirect("/found-items")

# =====================================================
# LOST ITEMS PAGE
# =====================================================

@app.route("/lost-items")
def lost_items_page():

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()


    query = {}


    if search:

        query["$or"] = [

            {
                "item_name": {
                    "$regex": search,
                    "$options": "i"
                }
            },

            {
                "description": {
                    "$regex": search,
                    "$options": "i"
                }
            },

            {
                "location": {
                    "$regex": search,
                    "$options": "i"
                }
            }

        ]


    if category:

        query["category"] = category


    items = list(
        lost_items.find(query)
    )


    return render_template(
        "lost_items.html",

        items=items,

        search=search,

        selected_category=category
    )


# =====================================================
# FOUND ITEMS PAGE
# =====================================================

@app.route("/found-items")
def found_items_page():

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()


    query = {}


    if search:

        query["$or"] = [

            {
                "item_name": {
                    "$regex": search,
                    "$options": "i"
                }
            },

            {
                "description": {
                    "$regex": search,
                    "$options": "i"
                }
            },

            {
                "location": {
                    "$regex": search,
                    "$options": "i"
                }
            }

        ]


    if category:

        query["category"] = category


    items = list(
        found_items.find(query)
    )


    return render_template(
        "found_items.html",

        items=items,

        search=search,

        selected_category=category
    )


# =====================================================
# MY REPORTS
# =====================================================

@app.route("/my-reports")
def my_reports():

    if "user_id" not in session:

        return redirect("/login")


    user_id = session["user_id"]


    my_lost_items = list(
        lost_items.find({
            "user_id": user_id
        })
    )


    my_found_items = list(
        found_items.find({
            "user_id": user_id
        })
    )


    return render_template(
        "my_reports.html",

        lost_items=my_lost_items,

        found_items=my_found_items
    )


# =====================================================
# LOST ITEM API - ADD
# =====================================================

@app.route(
    "/api/lost-items",
    methods=["POST"]
)
def add_lost_item_api():

    if "user_id" not in session:

        return {
            "message": "Please login first!"
        }, 401


    data = request.get_json()


    lost_items.insert_one({

        "item_name":
            data.get("item_name", ""),

        "description":
            data.get("description", ""),

        "location":
            data.get("location", ""),

        "category":
            data.get("category", "Other"),

        "image":
            data.get("image", ""),

        "user_id":
            session["user_id"],

        "user_name":
            session["user_name"],

        "user_email":
            session["user_email"]

    })


    return {
        "message":
            "Lost item added successfully!"
    }


# =====================================================
# LOST ITEM API - GET
# =====================================================

@app.route(
    "/api/lost-items",
    methods=["GET"]
)
def get_lost_items_api():

    items = list(
        lost_items.find(
            {},
            {
                "_id": 0
            }
        )
    )

    return items


# =====================================================
# LOST ITEM API - DELETE
# =====================================================

@app.route(
    "/api/lost-items/<item_id>",
    methods=["DELETE"]
)
def delete_lost_item(item_id):

    if "user_id" not in session:

        return {
            "message":
                "Please login first!"
        }, 401


    result = lost_items.delete_one({

        "_id": ObjectId(item_id),

        "user_id":
            session["user_id"]

    })


    if result.deleted_count == 0:

        return {
            "message":
                "You are not allowed to delete this item!"
        }, 403


    return {
        "message":
            "Lost item deleted successfully!"
    }


# =====================================================
# LOST ITEM API - UPDATE
# =====================================================

@app.route(
    "/api/lost-items/<item_id>",
    methods=["PUT"]
)
def update_lost_item(item_id):

    if "user_id" not in session:

        return {
            "message":
                "Please login first!"
        }, 401


    data = request.get_json()


    result = lost_items.update_one(

        {

            "_id":
                ObjectId(item_id),

            "user_id":
                session["user_id"]

        },

        {

            "$set": {

                "item_name":
                    data.get("item_name", ""),

                "description":
                    data.get("description", ""),

                "location":
                    data.get("location", ""),

                "category":
                    data.get("category", "Other")

            }

        }

    )


    if result.matched_count == 0:

        return {
            "message":
                "You are not allowed to edit this item!"
        }, 403


    return {
        "message":
            "Lost item updated successfully!"
    }


# =====================================================
# FOUND ITEM API - ADD
# =====================================================

@app.route(
    "/api/found-items",
    methods=["POST"]
)
def add_found_item_api():

    if "user_id" not in session:

        return {
            "message":
                "Please login first!"
        }, 401


    data = request.get_json()


    found_items.insert_one({

        "item_name":
            data.get("item_name", ""),

        "description":
            data.get("description", ""),

        "location":
            data.get("location", ""),

        "category":
            data.get("category", "Other"),

        "image":
            data.get("image", ""),

        "user_id":
            session["user_id"],

        "user_name":
            session["user_name"],

        "user_email":
            session["user_email"]

    })


    return {
        "message":
            "Found item added successfully!"
    }


# =====================================================
# FOUND ITEM API - GET
# =====================================================

@app.route(
    "/api/found-items",
    methods=["GET"]
)
def get_found_items_api():

    items = list(
        found_items.find(
            {},
            {
                "_id": 0
            }
        )
    )

    return items


# =====================================================
# FOUND ITEM API - DELETE
# =====================================================

@app.route(
    "/api/found-items/<item_id>",
    methods=["DELETE"]
)
def delete_found_item(item_id):

    if "user_id" not in session:

        return {
            "message":
                "Please login first!"
        }, 401


    result = found_items.delete_one({

        "_id":
            ObjectId(item_id),

        "user_id":
            session["user_id"]

    })


    if result.deleted_count == 0:

        return {
            "message":
                "You are not allowed to delete this item!"
        }, 403


    return {
        "message":
            "Found item deleted successfully!"
    }


# =====================================================
# FOUND ITEM API - UPDATE
# =====================================================

@app.route(
    "/api/found-items/<item_id>",
    methods=["PUT"]
)
def update_found_item(item_id):

    if "user_id" not in session:

        return {
            "message":
                "Please login first!"
        }, 401


    data = request.get_json()


    result = found_items.update_one(

        {

            "_id":
                ObjectId(item_id),

            "user_id":
                session["user_id"]

        },

        {

            "$set": {

                "item_name":
                    data.get("item_name", ""),

                "description":
                    data.get("description", ""),

                "location":
                    data.get("location", ""),

                "category":
                    data.get("category", "Other")

            }

        }

    )


    if result.matched_count == 0:

        return {
            "message":
                "You are not allowed to edit this item!"
        }, 403


    return {
        "message":
            "Found item updated successfully!"
    }

# =====================================================
# LOST ITEM - EDIT PAGE
# =====================================================

@app.route("/edit-lost/<item_id>", methods=["GET", "POST"])
def edit_lost(item_id):

    if "user_id" not in session:
        return redirect("/login")

    try:
        item = lost_items.find_one({
            "_id": ObjectId(item_id),
            "user_id": session["user_id"]
        })
    except:
        item = None

    if not item:
        flash(
            "You are not allowed to edit this item!",
            "error"
        )
        return redirect("/lost-items")

    if request.method == "POST":

        lost_items.update_one(
            {
                "_id": ObjectId(item_id),
                "user_id": session["user_id"]
            },
            {
                "$set": {
                    "item_name": request.form["item_name"],
                    "description": request.form["description"],
                    "location": request.form["location"],
                    "category": request.form.get(
                        "category",
                        "Other"
                    )
                }
            }
        )

        flash(
            "Lost item updated successfully!",
            "success"
        )

        return redirect("/lost-items")

    return render_template(
        "edit_lost.html",
        item=item
    )


# =====================================================
# LOST ITEM - DELETE
# =====================================================

@app.route(
    "/delete-lost/<item_id>",
    methods=["POST"]
)
def delete_lost(item_id):

    if "user_id" not in session:
        return redirect("/login")

    try:

        result = lost_items.delete_one({
            "_id": ObjectId(item_id),
            "user_id": session["user_id"]
        })

    except:

        result = None

    if not result or result.deleted_count == 0:

        flash(
            "You are not allowed to delete this item!",
            "error"
        )

        return redirect("/lost-items")

    flash(
        "Lost item deleted successfully!",
        "success"
    )

    return redirect("/lost-items")

# =====================================================
# FOUND ITEM - EDIT PAGE
# =====================================================

@app.route("/edit-found/<item_id>", methods=["GET", "POST"])
def edit_found(item_id):

    if "user_id" not in session:
        return redirect("/login")

    try:
        item = found_items.find_one({
            "_id": ObjectId(item_id),
            "user_id": session["user_id"]
        })
    except:
        item = None

    if not item:
        flash(
            "You are not allowed to edit this item!",
            "error"
        )
        return redirect("/found-items")

    if request.method == "POST":

        found_items.update_one(
            {
                "_id": ObjectId(item_id),
                "user_id": session["user_id"]
            },
            {
                "$set": {
                    "item_name": request.form["item_name"],
                    "description": request.form["description"],
                    "location": request.form["location"],
                    "category": request.form.get(
                        "category",
                        "Other"
                    )
                }
            }
        )

        flash(
            "Found item updated successfully!",
            "success"
        )

        return redirect("/found-items")

    return render_template(
        "edit_found.html",
        item=item
    )


# =====================================================
# FOUND ITEM - DELETE
# =====================================================

@app.route(
    "/delete-found/<item_id>",
    methods=["POST"]
)
def delete_found(item_id):

    if "user_id" not in session:
        return redirect("/login")

    try:

        result = found_items.delete_one({
            "_id": ObjectId(item_id),
            "user_id": session["user_id"]
        })

    except:

        result = None

    if not result or result.deleted_count == 0:

        flash(
            "You are not allowed to delete this item!",
            "error"
        )

        return redirect("/found-items")

    flash(
        "Found item deleted successfully!",
        "success"
    )

    return redirect("/found-items")

# =====================================================
# CONTACT REPORTER
# =====================================================

@app.route(
    "/contact/<item_type>/<item_id>"
)
def contact_reporter(
    item_type,
    item_id
):

    if "user_id" not in session:

        flash(
            "Please login to contact the reporter.",
            "error"
        )

        return redirect("/login")


    collection = (
        lost_items
        if item_type == "lost"
        else found_items
    )


    try:

        item = collection.find_one({
            "_id":
                ObjectId(item_id)
        })

    except:

        item = None


    if not item:

        flash(
            "Item not found!",
            "error"
        )

        return redirect("/")


    return render_template(
        "contact.html",
        item=item
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )