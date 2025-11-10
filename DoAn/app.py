
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CockroachDB Connection ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'cockroachdb://root@10.8.0.10:26257/doan_db?sslmode=disable'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True # Log SQL queries for debugging

db = SQLAlchemy(app)
ma = Marshmallow(app)

# --- Models (Updated for CockroachDB with BigInteger) ---
class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.BigInteger, primary_key=True)
    patient_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    test_forms = db.relationship('TestForm', backref='patient', cascade="all, delete-orphan")

class TestForm(db.Model):
    __tablename__ = 'test_form'
    id = db.Column(db.BigInteger, primary_key=True)
    form_number = db.Column(db.String(50), nullable=False)
    patient_id = db.Column(db.BigInteger, db.ForeignKey('patient.id'), nullable=False)
    test_details = db.relationship('TestDetail', backref='test_form', cascade="all, delete-orphan")

class TestDetail(db.Model):
    __tablename__ = 'test_detail'
    id = db.Column(db.BigInteger, primary_key=True)
    test_name = db.Column(db.String(100), nullable=False)
    result = db.Column(db.String(100))
    test_form_id = db.Column(db.BigInteger, db.ForeignKey('test_form.id'), nullable=False)

# --- Schemas (Updated to serialize BigInt as String) ---
class TestDetailSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(as_string=True)
    test_form_id = ma.auto_field(as_string=True)
    class Meta:
        model = TestDetail
        include_fk = True

class TestFormSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(as_string=True)
    patient_id = ma.auto_field(as_string=True)
    test_details = ma.Nested(TestDetailSchema, many=True)
    class Meta:
        model = TestForm
        include_fk = True

class PatientSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(as_string=True)
    test_forms = ma.Nested(TestFormSchema, many=True)
    class Meta:
        model = Patient
        include_fk = True

patient_schema = PatientSchema()
patients_schema = PatientSchema(many=True)
test_form_schema = TestFormSchema()
test_forms_schema = TestFormSchema(many=True)
test_detail_schema = TestDetailSchema()
test_details_schema = TestDetailSchema(many=True)

# --- Generic CRUD API (Updated for Large IDs) ---
def generate_crud_endpoints(model, schema, plural_schema, model_name):
    @app.route(f'/api/{model_name}', methods=['GET'], endpoint=f'{model_name}_get_all')
    def get_all():
        all_items = model.query.all()
        result = plural_schema.dump(all_items)
        return jsonify(result)

    @app.route(f'/api/{model_name}/<string:id>', methods=['GET'], endpoint=f'{model_name}_get_one')
    def get_one(id):
        item = model.query.get_or_404(int(id))
        return schema.jsonify(item)

    @app.route(f'/api/{model_name}', methods=['POST'], endpoint=f'{model_name}_create')
    def create():
        data = request.get_json()
        loaded_data = schema.load(data)
        new_item = model(**loaded_data)
        db.session.add(new_item)
        db.session.commit()
        return schema.jsonify(new_item), 201

    @app.route(f'/api/{model_name}/<string:id>', methods=['PUT'], endpoint=f'{model_name}_update')
    def update(id):
        item = model.query.get_or_404(int(id))
        data = request.get_json()
        loaded_data = schema.load(data, partial=True)
        for key, value in loaded_data.items():
            setattr(item, key, value)
        db.session.commit()
        return schema.jsonify(item)

    @app.route(f'/api/{model_name}/<string:id>', methods=['DELETE'], endpoint=f'{model_name}_delete')
    def delete(id):
        item = model.query.get_or_404(int(id))
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'})

generate_crud_endpoints(Patient, patient_schema, patients_schema, 'patients')
generate_crud_endpoints(TestForm, test_form_schema, test_forms_schema, 'test_forms')
generate_crud_endpoints(TestDetail, test_detail_schema, test_details_schema, 'test_details')

# --- Frontend Route ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
