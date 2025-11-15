
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import redis
import json

import uuid
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, func
from marshmallow import EXCLUDE

from flask import request, jsonify
from datetime import datetime
# from DoAn.appDiabetes import app, db, BenhNhan, LanKham

app = Flask(__name__)
CORS(app)

def _parse_date_any(s):
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

# --- Redis Connection with connection pooling ---
redis_pool = redis.ConnectionPool(
    host='10.8.0.10', 
    port=6379, 
    db=0, 
    decode_responses=True,
    max_connections=10,
    socket_keepalive=True,
    socket_connect_timeout=5,
    retry_on_timeout=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

# --- CockroachDB Connection ---
# Multi-node connection for high availability and load balancing
# Individual node URLs - application will try each until successful
CLUSTER_NODES = [
    'cockroachdb://root@10.8.0.10:26257/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App',
    'cockroachdb://root@10.8.0.11:26257/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App',
    'cockroachdb://root@10.8.0.12:26257/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App',
    'cockroachdb://root@10.8.0.13:26257/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App',
    'cockroachdb://root@10.8.0.14:26257/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App'
]

# For direct connection to specific node (used after successful health check)
def get_node_url(host, port=26257):
    """Build connection URL for specific node"""
    return f'cockroachdb://root@{host}:{port}/diabetesdb?sslmode=disable&application_name=DiabetesDB_Flask_App'

def get_active_connection():
    """Try to connect to any available node in the cluster"""
    from sqlalchemy import create_engine
    
    print(f"🔍 Scanning cluster for available nodes...")
    
    for i, node_url in enumerate(CLUSTER_NODES, 1):
        node_address = node_url.split('@')[1].split('/')[0]
        try:
            print(f"   Attempting node {i}: {node_address}")
            engine = create_engine(
                node_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                connect_args={
                    'connect_timeout': 5,
                    'options': '-c statement_timeout=30000'
                }
            )
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT node_id, address FROM crdb_internal.kv_node_status ORDER BY node_id"))
                nodes = result.fetchall()
                print(f"   ✅ Node {i} ({node_address}) is ONLINE")
                print(f"   📊 Cluster status: {', '.join([f'Node {n[0]} ({n[1]})' for n in nodes])}")
            engine.dispose()
            # Successfully connected - return this node URL
            return node_url
        except Exception as e:
            print(f"   ❌ Node {i} ({node_address}) is OFFLINE: {str(e)[:80]}")
            continue
    
    # If no nodes available, return None
    print(f"   ⚠️  All nodes are unreachable")
    return None

# Try to get an active connection
try:
    active_node = get_active_connection()
    
    if active_node:
        app.config['SQLALCHEMY_DATABASE_URI'] = active_node
        node_address = active_node.split('@')[1].split('?')[0]
        print(f"\n✨ Successfully connected to CockroachDB cluster")
        print(f"🎯 Active connection: {node_address}")
        print(f"🚀 Application ready to start!\n")
    else:
        print(f"\n⚠️  WARNING: No CockroachDB nodes are currently available")
        print(f"📍 Expected nodes: 10.8.0.10:26257, 10.8.0.14:26257")
        print(f"🔄 Application will start in LIMITED MODE")
        print(f"   - API endpoints will attempt auto-reconnection on each request")
        print(f"   - Please start at least one CockroachDB node")
        print(f"   - The app will automatically connect when a node becomes available\n")
        
        # Use fallback URL but don't fail - let before_request handle reconnection
        app.config['SQLALCHEMY_DATABASE_URI'] = CLUSTER_NODES[0]
        
except Exception as e:
    print(f"\n💥 CRITICAL ERROR during startup: {e}")
    print(f"⚠️  Starting in LIMITED MODE - will retry connections on requests\n")
    # Don't exit - let the app start and handle reconnection later
    app.config['SQLALCHEMY_DATABASE_URI'] = CLUSTER_NODES[0]

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True # Log SQL queries for debugging
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before using them
    'pool_recycle': 3600,   # Recycle connections after 1 hour
    'pool_size': 10,        # Connection pool size
    'max_overflow': 20,     # Max connections beyond pool_size
    'connect_args': {
        'application_name': 'DiabetesDB_Flask_App',
        'options': '-c statement_timeout=30000',
        'connect_timeout': 5
    }
}

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
    chieu_cao = db.Column(db.Float)
    can_nang = db.Column(db.Float)
    bmi = db.Column(db.Float)
    huyet_ap_tren = db.Column(db.Float)
    huyet_ap_duoi = db.Column(db.Float)
    duong_huyet = db.Column(db.Float)
    hba1c = db.Column(db.Float)
    diabetes = db.Column(db.Numeric(1, 0))
    mo_ta = db.Column(db.String(500))

class benhNhanSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(as_string=True, dump_only=True)
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
    id = ma.auto_field(as_string=True, dump_only=True)
    benh_nhan_id = ma.auto_field(as_string=True, data_key='idBenhNhan', required=False)
    bac_si = ma.auto_field(as_string=True, data_key='bacSi', required=False)
    class Meta:
        model = LanKham
        include_fk = True
        unknown = EXCLUDE

bnSchema = benhNhanSchema()
bnSchemas = benhNhanSchema(many=True)
lkSchema = lanKhamSchema()
lkSchemas = lanKhamSchema(many=True)

# --- Redis Helper Functions ---
def get_from_cache(key):
    """Safely get data from Redis cache"""
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"Redis connection error: {e}")
    except Exception as e:
        print(f"Redis error: {e}")
    return None

def set_to_cache(key, value, ttl=3600):
    """Safely set data to Redis cache"""
    try:
        redis_client.setex(key, ttl, json.dumps(value))
        return True
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"Redis connection error: {e}")
    except Exception as e:
        print(f"Redis error: {e}")
    return False

# --- CockroachDB Helper Functions ---
def get_node_connection(node_url):
    """Create a connection to a specific node"""
    from sqlalchemy import create_engine
    engine = create_engine(
        node_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={'connect_timeout': 5}
    )
    return engine

def test_node_connectivity():
    """Test connectivity to all cluster nodes"""
    results = {}
    for i, node_url in enumerate(CLUSTER_NODES, 1):
        try:
            engine = get_node_connection(node_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                results[f'node_{i}'] = {
                    'url': node_url.split('@')[1].split('/')[0],  # Extract host:port
                    'status': 'online',
                    'success': True
                }
            engine.dispose()
        except Exception as e:
            results[f'node_{i}'] = {
                'url': node_url.split('@')[1].split('/')[0],
                'status': 'offline',
                'success': False,
                'error': str(e)
            }
    return results

def reconnect_to_cluster():
    """Attempt to reconnect to any available node if current connection fails"""
    global db
    
    # Get current connection for logging
    current_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
    current_node = current_uri.split('@')[1].split('/')[0] if '@' in current_uri else 'unknown'
    
    print(f"📡 Current node ({current_node}) is unreachable")
    print(f"🔍 Scanning {len(CLUSTER_NODES)} nodes for available connection...")
    
    # Try each node
    for i, node_url in enumerate(CLUSTER_NODES, 1):
        node_address = node_url.split('@')[1].split('/')[0]
        
        # Skip current failed node
        if node_address in current_uri:
            print(f"   ⏭️  Skipping current failed node {i}: {node_address}")
            continue
            
        try:
            print(f"   🔌 Trying node {i}: {node_address}...")
            
            # Update the connection URL
            app.config['SQLALCHEMY_DATABASE_URI'] = node_url
            
            # Dispose old engine and create new one
            db.engine.dispose()
            from sqlalchemy import create_engine
            new_engine = create_engine(
                node_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                connect_args={
                    'connect_timeout': 5,
                    'options': '-c statement_timeout=30000'
                }
            )
            
            # Test new connection
            with new_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # If successful, update db.engine
            db.engine = new_engine
            
            print(f"   ✅ Successfully reconnected to node {i}: {node_address}")
            print(f"   🎯 Active connection: {node_address}")
            return True
            
        except Exception as retry_error:
            print(f"   ❌ Node {i} ({node_address}) failed: {retry_error}")
            continue
    
    print(f"💀 CRITICAL: All {len(CLUSTER_NODES)} nodes are unreachable!")
    return False

# Request error handler with auto-reconnect
@app.before_request
def before_request():
    """Check database connection before each request and auto-failover if needed"""
    try:
        # Quick health check with short timeout
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"⚠️ Database connection lost: {e}")
        print(f"🔄 Attempting automatic failover to another node...")
        
        # Try to reconnect to any available node
        if reconnect_to_cluster():
            print(f"✓ Successfully failed over to backup node")
            # Connection restored, continue with request
        else:
            from flask import jsonify
            return jsonify({
                'error': 'Database cluster unavailable',
                'message': 'All database nodes are unreachable. Please check cluster status.'
            }), 503

@app.errorhandler(Exception)
def handle_db_error(error):
    """Handle database errors with automatic failover"""
    error_str = str(error).lower()
    
    # Check if it's a connection error
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'refused', 'unreachable']):
        print(f"Database error detected: {error}")
        
        # Try to reconnect
        if reconnect_to_cluster():
            return jsonify({
                'error': 'Connection temporarily lost',
                'message': 'Successfully failed over to another node. Please retry your request.'
            }), 503
        else:
            return jsonify({
                'error': 'Database cluster unavailable',
                'message': 'All database nodes are unreachable'
            }), 503
    
    # For other errors, return generic error
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

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
    # Try to get from Redis cache
    cache_key = 'danhsachtinh'
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # If not in cache, query database
    rows = (db.session.query(
        dmTinh.ma_tinh.label('id'),
        func.trim(dmTinh.ten_tinh).label('ten')
    ).group_by(dmTinh.ma_tinh, dmTinh.ten_tinh)
            .order_by(func.trim(dmTinh.ten_tinh)).all())
    result = [{'id': r.id, 'ten': r.ten} for r in rows]
    
    # Cache for 1 hour (3600 seconds)
    set_to_cache(cache_key, result, 3600)
    
    return jsonify(result)

@app.route('/api/danhsachxa', methods=['GET'])
def danhsachxa():
    ma_tinh = request.args.get('ma_tinh', default='', type=str)
    
    # Try to get from Redis cache
    cache_key = f'danhsachxa:{ma_tinh}'
    cached_data = get_from_cache(cache_key)
    
    if cached_data:
        return jsonify(cached_data)
    
    # If not in cache, query database
    rows = (db.session.query(
        dmXa.ma_xa.label('id'),
        func.trim(dmXa.ten_xa).label('ten'),
        func.trim(dmXa.ten_xa).label('ten')
    ).filter(dmXa.ma_tinh == ma_tinh)
            .group_by(dmXa.ma_xa, dmXa.ten_xa, dmXa.ma_tinh)
            .order_by(func.trim(dmXa.ten_xa)).all())
    result = [{'id': r.id, 'ten': r.ten} for r in rows]
    
    # Cache for 1 hour (3600 seconds)
    set_to_cache(cache_key, result, 3600)
    
    return jsonify(result)
@app.route('/api/nocache/danhsachtinh', methods=['GET'])
def nocache_danhsachtinh():
    rows = (db.session.query(
        dmTinh.ma_tinh.label('id'),
        func.trim(dmTinh.ten_tinh).label('ten')
    ).group_by(dmTinh.ma_tinh, dmTinh.ten_tinh)
            .order_by(func.trim(dmTinh.ten_tinh)).all())
    result = [{'id': r.id, 'ten': r.ten} for r in rows]
    return jsonify(result)

@app.route('/api/nocache/danhsachxa', methods=['GET'])
def nocache_danhsachxa():
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

# Cache management endpoints
@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    try:
        data = request.get_json()
        cache_type = data.get('type', 'all')
        
        if cache_type == 'all':
            redis_client.flushdb()
            return jsonify({'message': 'Đã xóa toàn bộ cache', 'success': True})
        elif cache_type == 'tinh':
            redis_client.delete('danhsachtinh')
            return jsonify({'message': 'Đã xóa cache danh sách tỉnh', 'success': True})
        elif cache_type == 'xa':
            # Delete all xa cache keys
            keys = redis_client.keys('danhsachxa:*')
            if keys:
                redis_client.delete(*keys)
            return jsonify({'message': 'Đã xóa cache danh sách xã', 'success': True})
        else:
            return jsonify({'message': 'Loại cache không hợp lệ', 'success': False}), 400
    except (redis.ConnectionError, redis.TimeoutError) as e:
        return jsonify({'message': f'Lỗi kết nối Redis: {str(e)}', 'success': False}), 500
    except Exception as e:
        return jsonify({'message': f'Lỗi: {str(e)}', 'success': False}), 500

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    try:
        info = redis_client.info('stats')
        dbsize = redis_client.dbsize()
        
        # Check specific cache keys
        tinh_cached = redis_client.exists('danhsachtinh')
        xa_keys = redis_client.keys('danhsachxa:*')
        
        return jsonify({
            'success': True,
            'total_keys': dbsize,
            'tinh_cached': bool(tinh_cached),
            'xa_cached_count': len(xa_keys),
            'redis_info': {
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        })
    except (redis.ConnectionError, redis.TimeoutError) as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi kết nối Redis: {str(e)}',
            'total_keys': 0,
            'tinh_cached': False,
            'xa_cached_count': 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}',
            'total_keys': 0,
            'tinh_cached': False,
            'xa_cached_count': 0
        })

@app.route('/cache-test')
def cache_test():
    return render_template('cache-test.html')

@app.route('/distributed-test')
def distributed_test():
    return render_template('distributed-test.html')

# ===== CockroachDB Distributed System APIs =====

@app.route('/api/cluster/connectivity', methods=['GET'])
def cluster_connectivity():
    """Test connectivity to all cluster nodes"""
    try:
        results = test_node_connectivity()
        online_count = sum(1 for r in results.values() if r['success'])
        
        return jsonify({
            'success': True,
            'nodes': results,
            'online_count': online_count,
            'total_count': len(CLUSTER_NODES),
            'cluster_healthy': online_count > 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/nodes', methods=['GET'])
def cluster_nodes():
    """Get information about all nodes in the cluster"""
    try:
        # Join kv_node_status with kv_node_liveness for complete info
        query = text("""
            SELECT 
                s.node_id, 
                s.address, 
                s.locality, 
                s.server_version, 
                s.started_at, 
                s.updated_at,
                l.epoch,
                l.expiration,
                l.draining,
                l.membership
            FROM crdb_internal.kv_node_status s
            LEFT JOIN crdb_internal.kv_node_liveness l ON s.node_id = l.node_id
            ORDER BY s.node_id
        """)
        result = db.session.execute(query)
        nodes = []
        
        from datetime import datetime, timedelta
        
        for row in result:
            # Simplified logic: if node has liveness data and membership is active, it's live
            is_live = True
            is_draining = False
            membership_status = 'active'
            
            if row[9]:  # membership status exists
                membership_status = row[9]
                # Node is live only if membership is active AND not draining
                is_live = membership_status == 'active'
            
            if row[8] is not None:  # draining status
                is_draining = bool(row[8])
                # If draining, node is effectively dead
                if is_draining:
                    is_live = False
            
            # Calculate uptime
            uptime_str = 'Unknown'
            if row[4]:  # started_at
                try:
                    uptime_delta = datetime.now(row[4].tzinfo if hasattr(row[4], 'tzinfo') else None) - row[4]
                    hours = int(uptime_delta.total_seconds() // 3600)
                    if hours < 1:
                        uptime_str = f"{int(uptime_delta.total_seconds() // 60)} minutes"
                    elif hours < 24:
                        uptime_str = f"{hours} hours"
                    else:
                        days = hours // 24
                        uptime_str = f"{days} day{'s' if days > 1 else ''}"
                except:
                    uptime_str = 'Unknown'
            
            nodes.append({
                'node_id': row[0],
                'address': row[1],
                'locality': row[2] if row[2] else 'default',
                'server_version': row[3] if row[3] else 'unknown',
                'started_at': str(row[4]) if row[4] else None,
                'updated_at': str(row[5]) if row[5] else None,
                'uptime': uptime_str,
                'is_live': is_live,
                'is_available': is_live and not is_draining,
                'is_draining': is_draining,
                'membership': membership_status,
                'epoch': row[6] if row[6] else None
            })
        return jsonify({'success': True, 'nodes': nodes, 'count': len(nodes)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/ranges', methods=['GET'])
def cluster_ranges():
    """Get information about data ranges distribution"""
    try:
        query = text("""
            SELECT 
                range_id,
                start_key_pretty,
                end_key_pretty,
                replica_count,
                replicas,
                lease_holder,
                table_name
            FROM [SHOW RANGES FROM DATABASE diabetesdb WITH DETAILS]
            ORDER BY range_id
            LIMIT 50
        """)
        result = db.session.execute(query)
        ranges = []
        for row in result:
            replicas_list = []
            if row[4]:
                try:
                    replicas_list = list(row[4])
                except TypeError:
                    replicas_list = [r.strip() for r in str(row[4]).strip('{}').split(',') if r.strip()]
            ranges.append({
                'range_id': row[0],
                'start_key': row[1],
                'end_key': row[2],
                'replica_count': row[3],
                'replicas': replicas_list,
                'lease_holder': row[5],
                'table_name': row[6]
            })
        return jsonify({'success': True, 'ranges': ranges, 'count': len(ranges)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/replication', methods=['GET'])
def cluster_replication():
    """Get replication status"""
    try:
        query = text("""
            SELECT 
                count(*) as total_ranges,
                sum(CASE WHEN replica_count >= 2 THEN 1 ELSE 0 END) as replicated_ranges,
                avg(replica_count) as avg_replicas
            FROM (
                SELECT replica_count
                FROM [SHOW RANGES FROM DATABASE diabetesdb WITH DETAILS]
            ) AS ranges
        """)
        result = db.session.execute(query).fetchone()
        
        return jsonify({
            'success': True,
            'total_ranges': result[0],
            'replicated_ranges': result[1],
            'avg_replicas': float(result[2]) if result[2] else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/table-distribution', methods=['GET'])
def table_distribution():
    """Get table distribution across nodes"""
    try:
        query = text("""
            SELECT 
                table_name,
                count(*) as range_count,
                array_agg(DISTINCT lease_holder) as nodes
            FROM [SHOW RANGES FROM DATABASE diabetesdb WITH DETAILS]
            GROUP BY table_name
            ORDER BY table_name
        """)
        result = db.session.execute(query)
        tables = []
        for row in result:
            tables.append({
                'table_name': row[0],
                'range_count': row[1],
                'nodes': sorted([n for n in row[2] if n is not None]) if row[2] else []
            })
        return jsonify({'success': True, 'tables': tables})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/distributed-query', methods=['POST'])
def distributed_query():
    """Execute a distributed query and show execution plan"""
    try:
        data = request.get_json()
        query_type = data.get('query_type', 'benhnhan')
        
        if query_type == 'benhnhan':
            # Count patients across nodes
            query = text("""
                SELECT 
                    count(*) as total_patients,
                    count(DISTINCT ma_tinh) as provinces_count,
                    max(created_at) as latest_record
                FROM benhnhan
            """)
        elif query_type == 'lankham':
            # Count visits across nodes
            query = text("""
                SELECT 
                    count(*) as total_visits,
                    count(DISTINCT benh_nhan_id) as unique_patients,
                    max(ngay_kham) as latest_visit
                FROM lankham
            """)
        elif query_type == 'join':
            # Complex join query
            query = text("""
                SELECT 
                    count(DISTINCT b.id) as total_patients,
                    count(l.id) as total_visits,
                    avg(l.chieucao) as avg_height,
                    avg(l.cannang) as avg_weight
                FROM benhnhan b
                LEFT JOIN lankham l ON b.id = l.benh_nhan_id
            """)
        else:
            return jsonify({'success': False, 'error': 'Invalid query type'}), 400
        
        import time
        start_time = time.time()
        result = db.session.execute(query).fetchone()
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get explain plan
        explain_query = text(f"EXPLAIN {query}")
        explain_result = db.session.execute(explain_query)
        explain_plan = [row[0] for row in explain_result]
        
        return jsonify({
            'success': True,
            'execution_time_ms': round(execution_time, 2),
            'result': {
                'data': list(result) if result else [],
                'columns': list(result.keys()) if result else []
            },
            'explain_plan': explain_plan,
            'query_type': query_type
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/node-query/<int:node_id>', methods=['POST'])
def node_specific_query(node_id):
    """Execute query on specific node"""
    try:
        data = request.get_json()
        query_type = data.get('query_type', 'count')
        
        # Force query to specific node by setting session variable
        set_node = text(f"SET experimental_force_lookup_replicas_on_node = {node_id}")
        db.session.execute(set_node)
        
        import time
        start_time = time.time()
        
        if query_type == 'count':
            query = text("SELECT count(*) FROM benhnhan")
        elif query_type == 'recent':
            query = text("SELECT count(*) FROM benhnhan WHERE created_at > NOW() - INTERVAL '7 days'")
        else:
            query = text("SELECT count(*) FROM lankham")
        
        result = db.session.execute(query).fetchone()
        execution_time = (time.time() - start_time) * 1000
        
        # Reset setting
        reset = text("RESET experimental_force_lookup_replicas_on_node")
        db.session.execute(reset)
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'result': result[0] if result else 0,
            'execution_time_ms': round(execution_time, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/failover-test', methods=['POST'])
def failover_test():
    """Test failover scenario"""
    try:
        # Try to insert data and show which node handles it
        test_patient = BenhNhan(
            ho_ten='Test Failover Patient',
            gioi_tinh=1
        )
        db.session.add(test_patient)
        db.session.commit()
        
        # Check which node stored the data
        query = text("""
            SELECT lease_holder, replicas
            FROM crdb_internal.ranges
            WHERE database_name = 'diabetesdb'
            AND table_name = 'benhnhan'
            LIMIT 1
        """)
        result = db.session.execute(query).fetchone()
        
        # Delete test data
        db.session.delete(test_patient)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Failover test completed',
            'lease_holder': result[0] if result else None,
            'replicas': result[1] if result else []
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/patients-by-node/<int:node_id>', methods=['GET'])
def patients_by_node(node_id):
    """Get patients data from specific node (or nearest replica)"""
    try:
        import time
        start_time = time.time()

        # Get node information
        target_node = None
        node_info_query = text("""
            SELECT s.node_id, s.address
            FROM crdb_internal.kv_node_status s
            WHERE s.node_id = :node_id
        """)
        row = db.session.execute(node_info_query, {'node_id': node_id}).fetchone()
        if row:
            target_node = {
                'node_id': row[0],
                'address': row[1]
            }
        else:
            raise ValueError(f'Node {node_id} not found in cluster metadata')

        # Query to get patients with their location information
        # Note: CockroachDB automatically routes to optimal replicas
        # Using AS OF SYSTEM TIME follower_read_timestamp() allows reading from any replica
        query = text("""
            SELECT 
                b.id,
                b.ho_ten,
                b.ngay_sinh,
                b.gioi_tinh,
                b.so_dien_thoai,
                b.so_cmnd,
                t.ten_tinh,
                x.ten_xa,
                b.dia_chi,
                b.email,
                b.created_at,
                COUNT(l.id) as total_visits
            FROM benhnhan b
            LEFT JOIN dmtinh t ON b.ma_tinh = t.ma_tinh
            LEFT JOIN dmxa x ON b.ma_xa = x.ma_xa
            LEFT JOIN lankham l ON b.id = l.benh_nhan_id
            GROUP BY b.id, b.ho_ten, b.ngay_sinh, b.gioi_tinh, b.so_dien_thoai, 
                     b.so_cmnd, t.ten_tinh, x.ten_xa, b.dia_chi, b.email, b.created_at
            ORDER BY b.created_at DESC
            LIMIT 50
        """)

        result = db.session.execute(query).fetchall()
        execution_time = (time.time() - start_time) * 1000
        
        patients = []
        for row in result:
            patients.append({
                'id': str(row[0]),
                'ho_ten': row[1],
                'ngay_sinh': row[2].strftime('%Y-%m-%d') if row[2] else None,
                'gioi_tinh': 'Nam' if row[3] == 1 else 'Nữ' if row[3] == 0 else 'Khác',
                'so_dien_thoai': row[4],
                'so_cmnd': row[5],
                'tinh': row[6],
                'xa': row[7],
                'dia_chi': row[8],
                'email': row[9],
                'created_at': row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
                'total_visits': row[11]
            })
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'node': target_node,
            'execution_time_ms': round(execution_time, 2),
            'total': len(patients),
            'patients': patients
        })
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/patients-distributed', methods=['GET'])
def patients_distributed():
    """Get patients aggregated from all live nodes"""
    try:
        import time
        start_time = time.time()
        
        # Get list of live nodes
        nodes_query = text("""
            SELECT 
                ns.node_id,
                ns.address,
                nl.membership
            FROM crdb_internal.kv_node_status ns
            LEFT JOIN crdb_internal.kv_node_liveness nl ON ns.node_id = nl.node_id
            WHERE nl.membership = 'active'
        """)
        
        nodes_result = db.session.execute(nodes_query).fetchall()
        live_nodes = [{'node_id': row[0], 'address': row[1]} for row in nodes_result]
        
        # Query patients (CockroachDB will automatically distribute this across nodes)
        query = text("""
            SELECT 
                b.id,
                b.ho_ten,
                b.ngay_sinh,
                b.gioi_tinh,
                b.so_dien_thoai,
                b.so_cmnd,
                t.ten_tinh,
                x.ten_xa,
                b.dia_chi,
                b.email,
                b.created_at,
                COUNT(l.id) as total_visits
            FROM benhnhan b
            LEFT JOIN dmtinh t ON b.ma_tinh = t.ma_tinh
            LEFT JOIN dmxa x ON b.ma_xa = x.ma_xa
            LEFT JOIN lankham l ON b.id = l.benh_nhan_id
            GROUP BY b.id, b.ho_ten, b.ngay_sinh, b.gioi_tinh, b.so_dien_thoai, 
                     b.so_cmnd, t.ten_tinh, x.ten_xa, b.dia_chi, b.email, b.created_at
            ORDER BY b.created_at DESC
            LIMIT 50
        """)
        
        result = db.session.execute(query).fetchall()
        execution_time = (time.time() - start_time) * 1000
        
        patients = []
        for row in result:
            patients.append({
                'id': str(row[0]),
                'ho_ten': row[1],
                'ngay_sinh': row[2].strftime('%Y-%m-%d') if row[2] else None,
                'gioi_tinh': 'Nam' if row[3] == 1 else 'Nữ' if row[3] == 0 else 'Khác',
                'so_dien_thoai': row[4],
                'so_cmnd': row[5],
                'tinh': row[6],
                'xa': row[7],
                'dia_chi': row[8],
                'email': row[9],
                'created_at': row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
                'total_visits': row[11]
            })
        
        return jsonify({
            'success': True,
            'execution_time_ms': round(execution_time, 2),
            'total': len(patients),
            'patients': patients,
            'nodes_used': len(live_nodes),
            'live_nodes': live_nodes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cluster/consistency-check', methods=['GET'])
def consistency_check():
    """Check data consistency across nodes"""
    try:
        # Get counts from different system tables
        queries = {
            'benhnhan_count': text("SELECT count(*) FROM benhnhan"),
            'lankham_count': text("SELECT count(*) FROM lankham"),
            'range_count': text("""
                SELECT count(*) FROM crdb_internal.ranges 
                WHERE database_name = 'diabetesdb'
            """),
            'underreplicated': text("""
                SELECT count(*) FROM crdb_internal.ranges 
                WHERE database_name = 'diabetesdb'
                AND array_length(replicas, 1) < 2
            """)
        }
        
        results = {}
        for key, query in queries.items():
            result = db.session.execute(query).fetchone()
            results[key] = result[0] if result else 0
        
        return jsonify({
            'success': True,
            'consistency': results,
            'is_consistent': results['underreplicated'] == 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/lankham/search', methods=['GET'])
def search_lankham():
    benh_nhan_id = request.args.get('benhNhanId')

    if not benh_nhan_id:
        return jsonify({'error': 'benhNhanId is required'}), 400

    # Build query
    sql = """
        SELECT
            l.id, l.benh_nhan_id, l.ngay_kham, l.bac_si,
            l.chieu_cao, l.can_nang, l.bmi,
            l.huyet_ap_tren, l.huyet_ap_duoi,
            l.duong_huyet, l.hba1c, l.diabetes, l.mo_ta
        FROM lankham l
        WHERE l.benh_nhan_id = :benh_nhan_id
        ORDER BY l.ngay_kham DESC
    """

    params = {'benh_nhan_id': benh_nhan_id}
    result = db.session.execute(text(sql), params).fetchall()

    # Map to frontend keys
    out = []
    for row in result:
        out.append({
            "id": str(row[0]),
            "idBenhNhan": str(row[1]),
            "ngayKham": row[2].isoformat() if row[2] else None,
            "bacSi": row[3],
            "chieuCao": float(row[4]) if row[4] else None,
            "canNang": float(row[5]) if row[5] else None,
            "bmi": float(row[6]) if row[6] else None,
            "huyetApTren": float(row[7]) if row[7] else None,
            "huyetApDuoi": float(row[8]) if row[8] else None,
            "duongHuyet": float(row[9]) if row[9] else None,
            "hba1c": float(row[10]) if row[10] else None,
            "diabetes": int(row[11]) if row[11] is not None else None,
            "moTa": row[12]
        })

    return jsonify(out)

@app.route('/api/benhnhan/search', methods=['GET'])
def search_benhnhan():
    # Query params (all optional)
    q = request.args.get('q')
    ho_ten = request.args.get('hoTen')
    so_cmt = request.args.get('soCMT')
    so_dien_thoai = request.args.get('soDienThoai')
    ma_tinh = request.args.get('maTinh')
    ma_xa = request.args.get('maXa')
    ngay_kham = _parse_date_any(request.args.get('ngayKham'))

    # Build WHERE conditions
    conditions = []
    params = {}

    # If ngayKham is provided, prioritize it and join with lankham
    if ngay_kham:
        # Query with join for date filtering
        sql = """
            SELECT DISTINCT
                b.id, b.ho_ten, b.ngay_sinh, b.gioi_tinh,
                b.so_dien_thoai, b.so_cmnd, b.email,
                b.ma_tinh, b.ma_xa, b.dia_chi
            FROM benhnhan b
            INNER JOIN lankham l ON b.id = l.benh_nhan_id
        """

        # Add date condition (match whole day)
        conditions.append("DATE(l.ngay_kham) = DATE(:ngay_kham)")
        params['ngay_kham'] = ngay_kham

    else:
        # Query without join for other filters
        sql = """
            SELECT
                b.id, b.ho_ten, b.ngay_sinh, b.gioi_tinh,
                b.so_dien_thoai, b.so_cmnd, b.email,
                b.ma_tinh, b.ma_xa, b.dia_chi
            FROM benhnhan b
        """

    # Add other search conditions
    if q:
        conditions.append("(b.ho_ten ILIKE :q OR b.so_cmnd ILIKE :q OR b.so_dien_thoai ILIKE :q)")
        params['q'] = f"%{q}%"

    if ho_ten:
        conditions.append("b.ho_ten ILIKE :ho_ten")
        params['ho_ten'] = f"%{ho_ten}%"

    if so_cmt:
        conditions.append("b.so_cmnd ILIKE :so_cmt")
        params['so_cmt'] = f"%{so_cmt}%"

    if so_dien_thoai:
        conditions.append("b.so_dien_thoai ILIKE :so_dien_thoai")
        params['so_dien_thoai'] = f"%{so_dien_thoai}%"

    if ma_tinh:
        conditions.append("b.ma_tinh = :ma_tinh")
        params['ma_tinh'] = ma_tinh

    if ma_xa:
        conditions.append("b.ma_xa = :ma_xa")
        params['ma_xa'] = ma_xa

    # Add WHERE clause
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY b.ho_ten LIMIT 1000"

    # Execute query
    result = db.session.execute(text(sql), params).fetchall()

    # Map to frontend keys
    out = []
    for row in result:
        out.append({
            "id": str(row[0]),
            "hoTen": row[1],
            "namSinh": row[2].isoformat() if row[2] else None,
            "gioiTinh": int(row[3]) if row[3] is not None else None,
            "soDienThoai": row[4],
            "soCMT": row[5],
            "email": row[6],
            "maTinh": row[7],
            "maXa": row[8],
            "soNha": row[9]
        })

    return jsonify(out)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
