document.addEventListener('DOMContentLoaded', () => {
    let numPlayers = 2;
    const playersContainer = document.getElementById('players-container');
    const playerSelect = document.getElementById('num-players-select');
    const resetBtn = document.getElementById('reset-btn');
    const toast = document.getElementById('error-toast');

    const positionMaps = {
        2: ['pos-bottom', 'pos-top'],
        3: ['pos-bottom', 'pos-top-left', 'pos-top-right'],
        4: ['pos-bottom', 'pos-left', 'pos-top', 'pos-right'],
        5: ['pos-bottom', 'pos-bottom-left', 'pos-top-left', 'pos-top-right', 'pos-bottom-right'],
        6: ['pos-bottom', 'pos-bottom-left', 'pos-top-left', 'pos-top', 'pos-top-right', 'pos-bottom-right']
    };

    renderPlayers(numPlayers);

    playerSelect.addEventListener('change', (e) => {
        numPlayers = parseInt(e.target.value);
        renderPlayers(numPlayers);
    });

    resetBtn.addEventListener('click', resetHand);

    document.body.addEventListener('input', (e) => {
        if (e.target.classList.contains('card-input')) {
            handleCardInput(e.target);
        }
    });

    function handleCardInput(input) {
        const val = input.value;
        if (val.length === 2) {
            formatCardInput(input);

            // Auto-focus to next input in sequence
            const container = input.closest('.hole-cards') || input.closest('.board-slots');
            if (container) {
                const inputs = Array.from(container.querySelectorAll('input.card-input'));
                const currentIndex = inputs.indexOf(input);

                if (currentIndex < inputs.length - 1) {
                    // Move to next card in same container
                    inputs[currentIndex + 1].focus();
                } else if (container.classList.contains('hole-cards')) {
                    // Move to next player's first card
                    const currentPlayerIndex = parseInt(input.closest('.player-seat').id.split('-')[1]);
                    const nextPlayerSeat = document.getElementById(`seat-${currentPlayerIndex + 1}`);

                    if (nextPlayerSeat) {
                        const nextPlayerFirstCard = nextPlayerSeat.querySelector('.hole-cards input');
                        if (nextPlayerFirstCard) {
                            nextPlayerFirstCard.focus();
                        }
                    }
                    // If no next player, we stay on the current last input (natural stop)
                }
            }

            setTimeout(checkAndCalculate, 100);
        } else {
            input.style.background = '';
            input.style.color = '';
        }
    }

    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

        document.getElementById(tabId).classList.add('active');
        const btns = document.querySelectorAll('.nav-btn');
        if (tabId === 'live-odds') btns[0].classList.add('active');
        else btns[1].classList.add('active');
    }

    function toggleFold(index) {
        const seat = document.getElementById(`seat-${index}`);
        const btn = seat.querySelector('.fold-btn');
        const isFolded = seat.classList.contains('folded');

        if (isFolded) return;

        seat.classList.add('folded');
        btn.classList.add('active');
        btn.disabled = true;

        checkAndCalculate();
    }

    function renderPlayers(count) {
        playersContainer.innerHTML = '';
        const positions = positionMaps[count];

        for (let i = 0; i < count; i++) {
            const seat = document.createElement('div');
            seat.className = `player-seat ${positions[i]}`;
            seat.id = `seat-${i}`;

            seat.innerHTML = `
                <div class="seat-header">
                    <span class="player-name">Player ${i + 1}</span>
                    <button class="fold-btn" onclick="toggleFold(${i})">FOLD</button>
                </div>
                <div class="hole-cards">
                    <input type="text" class="card-input p-card" id="p${i}-c1" maxlength="2" placeholder="C1">
                    <input type="text" class="card-input p-card" id="p${i}-c2" maxlength="2" placeholder="C2">
                </div>
            `;
            playersContainer.appendChild(seat);
        }
    }

    function checkAndCalculate() {
        let allPlayerCardsFilled = true;
        for (let i = 0; i < numPlayers; i++) {
            const c1 = document.getElementById(`p${i}-c1`);
            const c2 = document.getElementById(`p${i}-c2`);
            const c1Valid = c1.classList.contains('valid-card');
            const c2Valid = c2.classList.contains('valid-card');

            if (!c1Valid || !c2Valid) {
                allPlayerCardsFilled = false;
                break;
            }
        }

        if (allPlayerCardsFilled) {
            calculateEquity();
        }
    }

    function formatCardInput(input) {
        const val = input.value.toUpperCase();
        const regex = /^[AKQJT98765432][SHDC]$/;

        if (regex.test(val)) {
            const suit = val[1].toLowerCase();
            input.value = val;
            input.setAttribute('data-suit', suit);
            input.classList.add('valid-card');
        } else {
            input.classList.remove('valid-card');
            input.removeAttribute('data-suit');
        }
    }

    async function calculateEquity() {
        showError(null);

        const hands = [];
        for (let i = 0; i < numPlayers; i++) {
            const c1 = document.getElementById(`p${i}-c1`).value;
            const c2 = document.getElementById(`p${i}-c2`).value;
            hands.push(`${c1} ${c2}`);
        }

        const boardInputs = Array.from(document.querySelectorAll('.board-input')).map(i => i.value);
        const folded = [];
        document.querySelectorAll('.player-seat').forEach((seat, idx) => {
            if (seat.classList.contains('folded')) folded.push(idx);
        });

        const payload = {
            num_players: numPlayers,
            hands: hands,
            board: boardInputs,
            folded: folded
        };

        try {
            const res = await fetch('/calculate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (data.error) {
                showError(data.error);
                if (data.player) highlightError(data.player);
            } else if (data.status === 'success') {
                updateUI(data);
            }

        } catch (e) {
            showError("Network or Server Error");
        }
    }

    function updateUI(data) {
        document.getElementById('current-street-display').innerText =
            `Street: ${data.street.charAt(0).toUpperCase() + data.street.slice(1)}`;

        const splitProb = (data.split_prob * 100).toFixed(1);
        const potStats = document.getElementById('pot-stats');
        document.getElementById('split-prob').innerText = splitProb + '%';
        potStats.style.display = parseFloat(splitProb) > 1.0 ? 'block' : 'none';

        const players = [];
        for (let i = 0; i < numPlayers; i++) {
            const eq = parseFloat((data.equities[i.toString()] * 100).toFixed(1));
            players.push({index: i, equity: eq});
        }
        players.sort((a, b) => b.equity - a.equity);

        const tableBody = document.getElementById('equity-table-body');
        tableBody.innerHTML = players.map(p => `
            <tr class="${p.equity === players[0].equity && p.equity > 0 ? 'leader' : ''}">
                <td>Player ${p.index + 1}</td>
                <td>${p.equity.toFixed(1)}%</td>
            </tr>
        `).join('');

        document.getElementById('equity-table').style.display = 'block';

        const winningEquity = players[0].equity;
        for (let i = 0; i < numPlayers; i++) {
            const seat = document.getElementById(`seat-${i}`);
            const eq = parseFloat((data.equities[i.toString()] * 100).toFixed(1));
            seat.classList.toggle('winner', eq >= winningEquity - 0.1 && eq > 0);
        }
    }

    function showError(msg) {
        if (!msg) {
            toast.style.display = 'none';
            return;
        }
        toast.innerText = msg;
        toast.style.display = 'block';
        setTimeout(() => toast.style.display = 'none', 5000);
    }

    function highlightError(playerNum) {
        const seat = document.getElementById(`seat-${playerNum - 1}`);
        seat.style.borderColor = 'var(--danger)';
        setTimeout(() => seat.style.borderColor = '', 2000);
    }

    function resetHand() {
        document.querySelectorAll('.card-input').forEach(inp => {
            inp.value = '';
            formatCardInput(inp);
        });
        document.querySelectorAll('.fold-btn').forEach(btn => {
            btn.classList.remove('active');
            btn.disabled = false;
            btn.closest('.player-seat').classList.remove('folded');
        });
        resetStats();
    }

    function resetStats() {
        document.querySelectorAll('.player-seat').forEach(el => el.classList.remove('winner'));
        document.getElementById('current-street-display').innerText = 'Street: Preflop';
        document.getElementById('pot-stats').style.display = 'none';
        document.getElementById('equity-table').style.display = 'none';
        document.getElementById('equity-table-body').innerHTML = '';
    }

    fetch('/preflop/meta')
        .then(res => res.json())
        .then(data => {
            const topList = document.getElementById('top-hands-list');
            const bottomList = document.getElementById('bottom-hands-list');

            topList.innerHTML = data.top_hands.map(h => `
                <li>${h.hand}: Eq ${h.equity} | Pct ${h.percentile}</li>
            `).join('');

            bottomList.innerHTML = data.bottom_hands.map(h => `
                <li>${h.hand}: Eq ${h.equity} | Pct ${h.percentile}</li>
            `).join('');
        })
        .catch(e => console.error("Could not load preflop meta data:", e));

    window.switchTab = switchTab;
    window.toggleFold = toggleFold;
});