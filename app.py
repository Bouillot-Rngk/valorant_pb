from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Our original BO3 state (9 steps internally) but we’ll combine actions for the overlay.
state = {
    "teamA": "Team A",
    "teamB": "Team B",
    "step": 0,  # Process is complete when step === 9.
    "bans": [],  # Expected: [ban1, ban2, ban3]
    "map1": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "map2": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "map3": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
    "available_maps": ["Abyss", "Bind", "Haven", "Fracture", "Lotus", "Pearl", "Split"]
}

@app.route('/')
def control_panel():
    return render_template('control_panel.html')

@app.route('/overlay')
def overlay():
    return render_template('overlay.html')

@socketio.on('update_action')
def handle_update_action(data):
    # Data may include "map" or "side" depending on the current step.
    map_val = data.get('map')
    side_val = data.get('side')
    
    if state['step'] == 0:
        # Action 1: Team A bans a map.
        if map_val in state['available_maps']:
            state['bans'].append({"team": state['teamA'], "map": map_val})
            state['available_maps'].remove(map_val)
            state['step'] = 1
    elif state['step'] == 1:
        # Action 2: Team B bans a map.
        if map_val in state['available_maps']:
            state['bans'].append({"team": state['teamB'], "map": map_val})
            state['available_maps'].remove(map_val)
            state['step'] = 2
    elif state['step'] == 2:
        # Action 3: Team A picks map for Map 1.
        if map_val in state['available_maps']:
            state['map1']["map"] = map_val
            state['map1']["map_picked_by"] = state['teamA']
            state['available_maps'].remove(map_val)
            state['step'] = 3
    elif state['step'] == 3:
        # Action 3 (continued): Team B picks side for Map 1.
        if side_val in ["attack", "defense"]:
            state['map1']["side"] = side_val
            state['map1']["side_picked_by"] = state['teamB']
            state['step'] = 4
    elif state['step'] == 4:
        # Action 4: Team B picks map for Map 2.
        if map_val in state['available_maps']:
            state['map2']["map"] = map_val
            state['map2']["map_picked_by"] = state['teamB']
            state['available_maps'].remove(map_val)
            state['step'] = 5
    elif state['step'] == 5:
        # Action 4 (continued): Team A picks side for Map 2.
        if side_val in ["attack", "defense"]:
            state['map2']["side"] = side_val
            state['map2']["side_picked_by"] = state['teamA']
            state['step'] = 6
    elif state['step'] == 6:
        # Action 5: Team A bans a map.
        if map_val in state['available_maps']:
            state['bans'].append({"team": state['teamA'], "map": map_val})
            state['available_maps'].remove(map_val)
            state['step'] = 7
    elif state['step'] == 7:
        # Action 6: Team B picks map for Map 3.
        if map_val in state['available_maps']:
            state['map3']["map"] = map_val
            state['map3']["map_picked_by"] = state['teamB']
            state['available_maps'].remove(map_val)
            state['step'] = 8
    elif state['step'] == 8:
        # Action 6 (continued): Team A picks side for Map 3.
        if side_val in ["attack", "defense"]:
            state['map3']["side"] = side_val
            state['map3']["side_picked_by"] = state['teamA']
            state['step'] = 9  # Process completed.
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
        "step": 0,
        "bans": [],
        "map1": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map2": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "map3": {"map": "TBD", "side": "TBD", "map_picked_by": "TBD", "side_picked_by": "TBD"},
        "available_maps": ["Abyss", "Bind", "Haven", "Fracture", "Lotus", "Pearl", "Split"]
    }
    emit('state_updated', state, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
