from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from app import app, db
from app.models import User, Account, TrustedContact, ExecutionLog


# helpers
def execute_plan_for_user(user):
    accounts = Account.query.filter_by(user_id=user.id).all()
    for acc in accounts:
        if acc.action == "delete":
            acc.status = "marked_for_deletion"
            log_action = "Marked for deletion"
        elif acc.action == "memorialize":
            acc.status = "memorialized"
            log_action = "Marked for memorialization"
        elif acc.action == "archive":
            acc.status = "archived"
            log_action = "Marked for archiving"
        else:
            acc.status = "no_change"
            log_action = "No action"

        log = ExecutionLog(
            user_id=user.id,
            account_id=acc.id,
            action_taken=f"{acc.service_name}: {log_action}",
        )
        db.session.add(log)

    user.is_deceased = True
    db.session.commit()


# basic pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    accounts_count = Account.query.filter_by(user_id=current_user.id).count()
    contacts_count = TrustedContact.query.filter_by(user_id=current_user.id).count()
    return render_template(
        "dashboard.html",
        accounts_count=accounts_count,
        contacts_count=contacts_count,
    )


# auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not full_name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email is already registered.")
            return redirect(url_for("register"))

        user = User(full_name=full_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# accounts
@app.route("/accounts")
@login_required
def manage_accounts():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template("accounts.html", accounts=accounts)


@app.route("/accounts/add", methods=["GET", "POST"])
@login_required
def add_account():
    if request.method == "POST":
        service_name = request.form.get("service_name")
        identifier = request.form.get("identifier")
        action = request.form.get("action")
        notes = request.form.get("notes")

        category_select = request.form.get("category_select")
        category_manual = request.form.get("category_manual")

        if category_select == "other":
            category = category_manual
        else:
            category = category_select

        if not service_name or not identifier or not action or not category:
            flash("Please fill all required fields.")
            return redirect(url_for("add_account"))

        acc = Account(
            service_name=service_name,
            category=category,
            identifier=identifier,
            action=action,
            notes=notes,
            user_id=current_user.id,
        )
        db.session.add(acc)
        db.session.commit()
        flash("Account added.")
        return redirect(url_for("manage_accounts"))

    return render_template("account_form.html", account=None)


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def edit_account(account_id):
    acc = Account.query.get_or_404(account_id)
    if acc.user_id != current_user.id:
        flash("You are not allowed to edit this account.")
        return redirect(url_for("manage_accounts"))

    if request.method == "POST":
        acc.service_name = request.form.get("service_name")
        acc.identifier = request.form.get("identifier")
        acc.action = request.form.get("action")
        acc.notes = request.form.get("notes")

        category_select = request.form.get("category_select")
        category_manual = request.form.get("category_manual")

        if category_select == "other":
            acc.category = category_manual
        else:
            acc.category = category_select

        if not acc.service_name or not acc.identifier or not acc.action or not acc.category:
            flash("Please fill all required fields.")
            return redirect(url_for("edit_account", account_id=acc.id))

        db.session.commit()
        flash("Account updated.")
        return redirect(url_for("manage_accounts"))

    return render_template("account_form.html", account=acc)


@app.route("/accounts/<int:account_id>/delete", methods=["POST"])
@login_required
def delete_account(account_id):
    acc = Account.query.get_or_404(account_id)
    if acc.user_id != current_user.id:
        flash("You are not allowed to delete this account.")
        return redirect(url_for("manage_accounts"))

    db.session.delete(acc)
    db.session.commit()
    flash("Account deleted.")
    return redirect(url_for("manage_accounts"))


# contacts
@app.route("/contacts")
@login_required
def manage_contacts():
    contacts = TrustedContact.query.filter_by(user_id=current_user.id).all()
    return render_template("contacts.html", contacts=contacts)


@app.route("/contacts/add", methods=["GET", "POST"])
@login_required
def add_contact():
    if request.method == "POST":
        name = request.form.get("name")
        relationship = request.form.get("relationship")
        email = request.form.get("email")
        is_primary = bool(request.form.get("is_primary"))

        if not name or not email:
            flash("Name and email are required.")
            return redirect(url_for("add_contact"))

        c = TrustedContact(
            name=name,
            relationship=relationship,
            email=email,
            is_primary=is_primary,
            user_id=current_user.id,
        )
        db.session.add(c)
        db.session.commit()
        flash("Trusted contact added.")
        return redirect(url_for("manage_contacts"))

    return render_template("contact_form.html", contact=None)


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
@login_required
def edit_contact(contact_id):
    c = TrustedContact.query.get_or_404(contact_id)
    if c.user_id != current_user.id:
        flash("You are not allowed to edit this contact.")
        return redirect(url_for("manage_contacts"))

    if request.method == "POST":
        c.name = request.form.get("name")
        c.relationship = request.form.get("relationship")
        c.email = request.form.get("email")
        c.is_primary = bool(request.form.get("is_primary"))

        if not c.name or not c.email:
            flash("Name and email are required.")
            return redirect(url_for("edit_contact", contact_id=c.id))

        db.session.commit()
        flash("Contact updated.")
        return redirect(url_for("manage_contacts"))

    return render_template("contact_form.html", contact=c)


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
def delete_contact(contact_id):
    c = TrustedContact.query.get_or_404(contact_id)
    if c.user_id != current_user.id:
        flash("You are not allowed to delete this contact.")
        return redirect(url_for("manage_contacts"))

    db.session.delete(c)
    db.session.commit()
    flash("Contact deleted.")
    return redirect(url_for("manage_contacts"))


# plan + self simulation
@app.route("/plan")
@login_required
def view_plan():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    contacts = TrustedContact.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "plan.html",
        accounts=accounts,
        contacts=contacts,
    )


@app.route("/plan/execute", methods=["POST"])
@login_required
def execute_plan():
    execute_plan_for_user(current_user)
    flash("Your digital legacy plan has been executed (simulation).")
    return redirect(url_for("execution_result"))


@app.route("/plan/execution_result")
@login_required
def execution_result():
    logs = ExecutionLog.query.filter_by(user_id=current_user.id).order_by(ExecutionLog.timestamp.desc()).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template("execution_result.html", logs=logs, accounts=accounts)


# executor portal
@app.route("/executor", methods=["GET", "POST"])
def executor_portal():
    if request.method == "POST":
        contact_email = request.form.get("contact_email")
        deceased_email = request.form.get("deceased_email")
        message = request.form.get("message")

        if not contact_email or not deceased_email:
            flash("Both email fields are required.")
            return redirect(url_for("executor_portal"))

        deceased = User.query.filter_by(email=deceased_email).first()
        if not deceased:
            flash("No user found with that email.")
            return redirect(url_for("executor_portal"))

        trusted = TrustedContact.query.filter_by(user_id=deceased.id, email=contact_email).first()
        if not trusted:
            flash("You are not registered as a trusted contact for this user.")
            return redirect(url_for("executor_portal"))

        execute_plan_for_user(deceased)

        accounts = Account.query.filter_by(user_id=deceased.id).all()
        logs = ExecutionLog.query.filter_by(user_id=deceased.id).order_by(ExecutionLog.timestamp.desc()).all()

        return render_template(
            "executor_execution_result.html",
            deceased=deceased,
            accounts=accounts,
            logs=logs,
            message=message,
        )

    return render_template("executor.html")
