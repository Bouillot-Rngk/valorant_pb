from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from prometheus_client import Counter, Summary, Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import eventlet
import psutil

try:
    from monotonic import monotonic
except ImportError:
    from time import monotonic


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, async_mode='eventlet')

# Prometheus Metrics
REQUEST_COUNT = Counter('flask_request_count', 'Total Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Summary('flask_request_latency_seconds', 'Request latency in seconds', ['endpoint'])
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percent')

@app.before_request
def start_timer():
    request.start_time = monotonic()

@app.after_request
def record_metrics(response):
    latency = monotonic() - request.start_time
    REQUEST_LATENCY.labels(request.path).observe(latency)
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response

# Background task for updating CPU usage metric
def update_cpu_usage():
    while True:
        CPU_USAGE.set(psutil.cpu_percent())
        eventlet.sleep(5)

# Start CPU usage monitoring in the background
eventlet.spawn(update_cpu_usage)

# Expose Prometheus metrics at the /metrics endpoint
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# --- Original App Code Below ---

# Original Pick/Ban State
state = {
    "teamA": "Team A",
    "teamB": "Team B",
    "boType": 3,         # default BO type; this will be updated from the control panel
    "step": 0,
    "bans": [],
    "map1": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "map2": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "map3": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    # For BO5, we will need 5 maps. We add placeholders:
    "map4": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "map5": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    # "available_maps": ["Abyss", "Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox",  "Lotus", "Pearl", "Split", "Sunset"]
    "available_maps": ["Ascent", "Fracture", "Haven", "Icebox",  "Lotus", "Pearl", "Split"]
    # "available_maps": ["Abyss", "Bind", "Haven", "Fracture", "Lotus", "Pearl", "Split"]
}

# BO Tracking State – built from the above state when PB is complete.
boTrackingState = {
    "boType": 3,  # This will mirror state.boType
    "currentMapIndex": 1,  # For BO3, default current is map1 of the tracking state; for BO5, valid indices are 0..4.
    "seriesScoreA": "0",
    "seriesScoreB": "0",
    # For BO3, we'll use maps 1-3; for BO5, maps 1-5.
    "maps": [
        {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "upcoming"},
        {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "current"},
        {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "upcoming"}
    ]
}

@app.route('/')
def control_panel():
    return render_template('control_panel.html')

@app.route('/overlay')
def overlay():
    return render_template('overlay.html')

@app.route('/bo_tracking')
def bo_tracking():
    return render_template('bo_tracking.html')

@app.route('/score_overlay')
def score_overlay():
    return render_template('score_overlay.html')

# --- Pick/Ban Socket.IO events ---
@socketio.on('update_action')
def handle_update_action(data):
    if "boType" in data:
        state["boType"] = int(data["boType"])
    map_val = data.get('map')
    side_val = data.get('side')
    
    # Branch logic based on boType:
    if state["boType"] == 3:
        # BO3 process:
        if state['step'] == 0:
            if map_val in state['available_maps']:
                state['bans'].append({"team": state['teamA'], "map": map_val})
                state['available_maps'].remove(map_val)
                state['step'] = 1
        elif state['step'] == 1:
            if map_val in state['available_maps']:
                state['bans'].append({"team": state['teamB'], "map": map_val})
                state['available_maps'].remove(map_val)
                state['step'] = 2
        elif state['step'] == 2:
            if map_val in state['available_maps']:
                state['map1']["map"] = map_val
                state['map1']["map_picked_by"] = state['teamA']
                state['available_maps'].remove(map_val)
                state['step'] = 3
        elif state['step'] == 3:
            if side_val in ["attack", "defense"]:
                state['map1']["side"] = side_val
                state['map1']["side_picked_by"] = state['teamB']
                state['step'] = 4
        elif state['step'] == 4:
            if map_val in state['available_maps']:
                state['map2']["map"] = map_val
                state['map2']["map_picked_by"] = state['teamB']
                state['available_maps'].remove(map_val)
                state['step'] = 5
        elif state['step'] == 5:
            if side_val in ["attack", "defense"]:
                state['map2']["side"] = side_val
                state['map2']["side_picked_by"] = state['teamA']
                state['step'] = 6
        elif state['step'] == 6:
            if map_val in state['available_maps']:
                state['bans'].append({"team": state['teamA'], "map": map_val})
                state['available_maps'].remove(map_val)
                state['step'] = 7
        elif state['step'] == 7:
            if map_val in state['available_maps']:
                state['map3']["map"] = map_val
                state['map3']["map_picked_by"] = state['teamB']
                state['available_maps'].remove(map_val)
                state['step'] = 8
        elif state['step'] == 8:
            if side_val in ["attack", "defense"]:
                state['map3']["side"] = side_val
                state['map3']["side_picked_by"] = state['teamA']
                state['step'] = 9
        # BO3 complete.
    else:
        # BO5 process:
        if state['step'] == 0:
            if map_val in state['available_maps']:
                state['bans'].append({"team": state['teamA'], "map": map_val})
                state['available_maps'].remove(map_val)
                state['step'] = 1
        elif state['step'] == 1:
            if map_val in state['available_maps']:
                state['bans'].append({"team": state['teamB'], "map": map_val})
                state['available_maps'].remove(map_val)
                state['step'] = 2
        elif state['step'] == 2:
            if map_val in state['available_maps']:
                state['map1']["map"] = map_val
                state['map1']["map_picked_by"] = state['teamA']
                state['available_maps'].remove(map_val)
                state['step'] = 3
        elif state['step'] == 3:
            if side_val in ["attack", "defense"]:
                state['map1']["side"] = side_val
                state['map1']["side_picked_by"] = state['teamB']
                state['step'] = 4
        elif state['step'] == 4:
            if map_val in state['available_maps']:
                state['map2']["map"] = map_val
                state['map2']["map_picked_by"] = state['teamB']
                state['available_maps'].remove(map_val)
                state['step'] = 5
        elif state['step'] == 5:
            if side_val in ["attack", "defense"]:
                state['map2']["side"] = side_val
                state['map2']["side_picked_by"] = state['teamA']
                state['step'] = 6
        elif state['step'] == 6:
            if map_val in state['available_maps']:
                state['map3']["map"] = map_val
                state['map3']["map_picked_by"] = state['teamA']
                state['available_maps'].remove(map_val)
                state['step'] = 7
        elif state['step'] == 7:
            if side_val in ["attack", "defense"]:
                state['map3']["side"] = side_val
                state['map3']["side_picked_by"] = state['teamB']
                state['step'] = 8
        elif state['step'] == 8:
            if map_val in state['available_maps']:
                state['map4']["map"] = map_val
                state['map4']["map_picked_by"] = state['teamB']
                state['available_maps'].remove(map_val)
                state['step'] = 9
        elif state['step'] == 9:
            if side_val in ["attack", "defense"]:
                state['map4']["side"] = side_val
                state['map4']["side_picked_by"] = state['teamA']
                state['step'] = 10
        elif state['step'] == 10:
            if map_val in state['available_maps']:
                state['map5']["map"] = map_val
                state['map5']["map_picked_by"] = state['teamB']
                state['available_maps'].remove(map_val)
                state['step'] = 11
        elif state['step'] == 11:
            if side_val in ["attack", "defense"]:
                state['map5']["side"] = side_val
                state['map5']["side_picked_by"] = state['teamA']
                state['step'] = 12  # Process complete.
    emit('state_updated', state, broadcast=True)

@socketio.on('update_teams')
def handle_update_teams(data):
    state['teamA'] = data.get('teamA') or "Team A"
    state['teamB'] = data.get('teamB') or "Team B"
    emit('state_updated', state, broadcast=True)

@socketio.on('reset_state')
def handle_reset_state():
    global state
    state = {
        "teamA": "Team A",
        "teamB": "Team B",
        "boType": 3,
        "step": 0,
        "bans": [],
        "map1": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map2": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map3": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map4": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map5": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "available_maps": ["Abyss", "Bind", "Haven", "Fracture", "Lotus", "Pearl", "Split"]
    }
    emit('state_updated', state, broadcast=True)

# --- BO Tracking Socket.IO events ---
@socketio.on('update_bo_tracking')
def handle_update_bo_tracking(data):
    global boTrackingState
    boTrackingState['boType'] = int(data.get('boType', 3))
    boTrackingState['currentMapIndex'] = int(data.get('currentMapIndex', 1))
    boTrackingState['seriesScoreA'] = data.get('seriesScoreA', "0")
    boTrackingState['seriesScoreB'] = data.get('seriesScoreB', "0")
    # Update maps for BO3 vs BO5:
    if boTrackingState['boType'] == 3:
        boTrackingState['maps'] = [
            {
                "map": state["map1"]["map"],
                "pickedBy": state["map1"]["map_picked_by"],
                "side": state["map1"]["side"],
                "score": data.get("score1", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map2"]["map"],
                "pickedBy": state["map2"]["map_picked_by"],
                "side": state["map2"]["side"],
                "score": data.get("score2", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map3"]["map"],
                "pickedBy": state["map3"]["map_picked_by"],
                "side": state["map3"]["side"],
                "score": data.get("score3", "TBD"),
                "status": "finished"
            }
        ]
    else:  # BO5
        boTrackingState['maps'] = [
            {
                "map": state["map1"]["map"],
                "pickedBy": state["map1"]["map_picked_by"],
                "side": state["map1"]["side"],
                "score": data.get("score1", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map2"]["map"],
                "pickedBy": state["map2"]["map_picked_by"],
                "side": state["map2"]["side"],
                "score": data.get("score2", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map3"]["map"],
                "pickedBy": state["map3"]["map_picked_by"],
                "side": state["map3"]["side"],
                "score": data.get("score3", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map4"]["map"],
                "pickedBy": state["map4"]["map_picked_by"],
                "side": state["map4"]["side"],
                "score": data.get("score4", "TBD"),
                "status": "finished"
            },
            {
                "map": state["map5"]["map"],
                "pickedBy": state["map5"]["map_picked_by"],
                "side": state["map5"]["side"],
                "score": data.get("score5", "TBD"),
                "status": "finished"
            }
        ]
    # Also copy team names from PB state.
    boTrackingState['teamA'] = state['teamA']
    boTrackingState['teamB'] = state['teamB']
    emit('tracking_state_updated', boTrackingState, broadcast=True)

@socketio.on('reset_bo_tracking')
def handle_reset_bo_tracking():
    global boTrackingState
    boTrackingState = {
      "boType": 3,
      "currentMapIndex": 1,
      "seriesScoreA": "0",
      "seriesScoreB": "0",
      "maps": [
          {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "upcoming"},
          {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "current"},
          {"map": "TBD", "pickedBy": "TBD", "side": "TBD", "score": "TBD", "status": "upcoming"}
      ]
    }
    emit('tracking_state_updated', boTrackingState, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
