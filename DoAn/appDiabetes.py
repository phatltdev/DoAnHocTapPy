
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

import uuid
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, func
from marshmallow import EXCLUDE
app = Flask(__name__)
CORS(app)

# --- CockroachDB Connection ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'cockroachdb://root@10.8.0.10:26257/diabetesdb?sslmode=disable'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True # Log SQL queries for debugging

db = SQLAlchemy(app)
ma = Marshmallow(app)

class dmTinh(db.Model):
    __tablename__ = 'dmtinh'
    ma_tinh = db.Column(db.String(10), primary_key=True)
    ten_tinh = db.Column(db.String(1000), nullable=False)
    
class dmXa(db.Model):
    __tablename__ = 'dmxa'
    ma_xa = db.Column(db.String(10), primary_key=True)
    ten_xa = db.Column(db.String(1000), nullable=False)
    ma_tinh = db.Column(db.String(10), db.ForeignKey('dmtinh.ma_tinh'), nullable=False)

class BenhNhan(db.Model):
    __tablename__ = 'benhnhan'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text('gen_random_uuid()'))
    ho_ten = db.Column(db.String(500), nullable=False)
    ngay_sinh = db.Column(db.Date)
    gioi_tinh = db.Column(db.Numeric(1, 0))
    so_dien_thoai = db.Column(db.String(20))
    so_cmnd = db.Column(db.String(20))
    ma_tinh = db.Column(db.String(10))
    ma_xa = db.Column(db.String(10))
    dia_chi = db.Column(db.String(500))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('now()'), nullable=False)
    phieu_tests = db.relationship('LanKham', backref='benhnhan', cascade="all, delete-orphan")

class LanKham(db.Model):
    __tablename__ = 'lankham'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text('gen_random_uuid()'))
    benh_nhan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('benhnhan.id'), nullable=False)
    ngay_kham = db.Column(db.DateTime(timezone=True), server_default=text('now()'), nullable=False)
    bac_si = db.Column(db.String(100))
    chieuCao = db.Column(db.Float)
    canNang = db.Column(db.Float)
    chisoBMI = db.Column(db.Float)
    huyetApTren = db.Column(db.String(20))
    huyetApDuoi = db.Column(db.String(20))
    diabetes = db.Column(db.Numeric(1, 0))
    mo_ta = db.Column(db.String(500))

class benhNhanSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    ho_ten = ma.auto_field(data_key='hoTen', required=True)
    ngay_sinh = ma.auto_field(data_key='namSinh')
    gioi_tinh = ma.auto_field(data_key='gioiTinh')
    so_cmnd = ma.auto_field(data_key='soCMT')
    so_dien_thoai = ma.auto_field(data_key='soDienThoai')
    ma_tinh = ma.auto_field(data_key='maTinh')
    ma_xa = ma.auto_field(data_key='maXa')
    dia_chi = ma.auto_field(data_key='soNha')
    phieu_tests = ma.Nested('lanKhamSchema', many=True, dump_only=True)

    class Meta:
        model = BenhNhan
        include_fk = True
        unknown = EXCLUDE


class lanKhamSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    benh_nhan_id = ma.auto_field(as_string=True, data_key='benhNhanId')

    class Meta:
        model = LanKham
        include_fk = True
        unknown = EXCLUDE

bnSchema = benhNhanSchema()
bnSchemas = benhNhanSchema(many=True)
lkSchema = lanKhamSchema()
lkSchemas = lanKhamSchema(many=True)
# --- Generic CRUD API (Updated for Large IDs) ---
def generate_crud_endpoints(model, schema, plural_schema, model_name):
    @app.route(f'/api/{model_name}', methods=['GET'], endpoint=f'{model_name}_get_all')
    def get_all():
        query = model.query
        created_col = getattr(model, 'ho_ten', None)
        if created_col is not None:
            # change to .asc() if you prefer oldest-first
            query = query.order_by(created_col.desc())
        all_items = query.all()
        result = plural_schema.dump(all_items)
        return jsonify(result)

    @app.route(f'/api/{model_name}/<string:id>', methods=['GET'], endpoint=f'{model_name}_get_one')
    def get_one(id):
        item = model.query.get_or_404(id)
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
        item = model.query.get_or_404(id)
        data = request.get_json()
        loaded_data = schema.load(data, partial=True)
        for key, value in loaded_data.items():
            setattr(item, key, value)
        db.session.commit()
        return schema.jsonify(item)

    @app.route(f'/api/{model_name}/<string:id>', methods=['DELETE'], endpoint=f'{model_name}_delete')
    def delete(id):
        item = model.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'})

generate_crud_endpoints(BenhNhan, bnSchema, bnSchemas, 'benhnhan')
generate_crud_endpoints(LanKham, lkSchema, lkSchemas, 'lankham')


@app.route('/')
def index():
    # return render_template('diabetesdb.html')
    return render_template('kham-benh-main.html')
@app.route('/api/danhsachtinh', methods=['GET'])
def danhsachtinh():
    rows = (db.session.query(
        dmTinh.ma_tinh.label('id'),
        func.trim(dmTinh.ten_tinh).label('ten')
    ).group_by(dmTinh.ma_tinh, dmTinh.ten_tinh)
            .order_by(func.trim(dmTinh.ten_tinh)).all())
    result = [{'id': r.id, 'ten': r.ten} for r in rows]
    return jsonify(result)

@app.route('/api/danhsachxa', methods=['GET'])
def danhsachxa():
    ma_tinh = request.args.get('ma_tinh', default='', type=str)
    rows = (db.session.query(
        dmXa.ma_xa.label('id'),
        func.trim(dmXa.ten_xa).label('ten'),
        func.trim(dmXa.ten_xa).label('ten')
    ).filter(dmXa.ma_tinh == ma_tinh)
            .group_by(dmXa.ma_xa, dmXa.ten_xa, dmXa.ma_tinh)
            .order_by(func.trim(dmXa.ten_xa)).all())
    result = [{'id': r.id, 'ten': r.ten} for r in rows]
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
