import sys
import os
from flask import Flask, render_template, request, jsonify
from src.live_odds import LiveOddsCalculator, parse_cards_string

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate_odds():
    try:
        data = request.json
        num_players = int(data.get('num_players', 2))
        raw_hands = data.get('hands', [])
        raw_board = data.get('board', [])
        folded_indices = data.get('folded', [])

        calc = LiveOddsCalculator(num_players)

        for i, hand_str in enumerate(raw_hands):
            if i >= num_players:
                break

            if not hand_str.strip():
                return jsonify({'status': 'incomplete', 'message': f'Player {i + 1} needs cards.'}), 200

            try:
                cards = parse_cards_string(hand_str)
                calc.add_player_hand(cards)
            except ValueError as ve:
                return jsonify({'error': str(ve), 'player': i + 1}), 400

        if raw_board:
            full_board_str = " ".join([b for b in raw_board if b.strip()])
            if full_board_str:
                board_cards = parse_cards_string(full_board_str)
                count = len(board_cards)

                if count >= 3:
                    calc.deal_flop(board_cards[:3])
                if count >= 4:
                    calc.deal_turn(board_cards[3])
                if count == 5:
                    calc.deal_river(board_cards[4])

        for idx in folded_indices:
            try:
                calc.fold_player(idx)
            except ValueError:
                pass

        equities = calc.calculate_equities(num_sims=10000)

        response = {
            'status': 'success',
            'equities': equities,
            'win_probs': calc.last_outright_win_probabilities,
            'split_prob': calc.last_split_probability,
            'street': calc.street
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f"Server Error: {str(e)}"}), 500


@app.route('/preflop/meta', methods=['GET'])
def preflop_meta():
    return jsonify({
        'heatmap_url': '/static/outputs/preflop_equity_heatmap.png',
        'top_hands': [
            {'hand': 'AA', 'equity': '85.2%', 'percentile': '99.9'},
            {'hand': 'KK', 'equity': '82.4%', 'percentile': '99.5'},
            {'hand': 'QQ', 'equity': '79.9%', 'percentile': '99.0'},
        ],
        'bottom_hands': [
            {'hand': '72o', 'equity': '29.2%', 'percentile': '0.5'},
            {'hand': '32o', 'equity': '31.1%', 'percentile': '1.2'},
        ]
    })


if __name__ == '__main__':
    app.run(debug=True, port=5003)

'''
TODO:
- Display hand names after river card
'''
