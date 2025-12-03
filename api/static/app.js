document.addEventListener('DOMContentLoaded', () => {
    let numPlayers = 2;
    const playersContainer = document.getElementById('players-container');
    const playerSelect = document.getElementById('num-players-select');
    const resetBtn = document.getElementById('reset-btn');
    const toast = document.getElementById('error-toast');

    const suitSymbols = {
        's': '♠', 'h': '♥', 'd': '♦', 'c': '♣'
    };


    // Card Picker State
    const usedCards = new Set(); // Tracks which cards are already used (e.g., "AS", "KH")
    let activeCardInput = null; // Tracks which input slot is waiting for card selection

    const ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
    const suits = ['s', 'h', 'd', 'c'];

    // Initialize card picker grid
    function initCardPicker() {
        const deckGrid = document.getElementById('deck-grid');
        if (!deckGrid) return;

        deckGrid.innerHTML = '';

        ranks.forEach(rank => {
            suits.forEach(suit => {
                const cardId = `${rank}${suit.toUpperCase()}`;
                const suitSymbol = suitSymbols[suit];
                const colorClass = (suit === 'h' || suit === 'd') ? 'card-red' : 'card-black';

                const button = document.createElement('button');
                button.className = 'deck-card';
                button.dataset.card = cardId;
                button.innerHTML = `
                    <span class="deck-card-rank ${colorClass}">${rank}</span>
                    <span class="deck-card-suit ${colorClass}">${suitSymbol}</span>
                `;
                button.onclick = () => selectCardFromPicker(cardId);

                deckGrid.appendChild(button);
            });
        });
    }

    // Select card from picker and fill active input
    function selectCardFromPicker(cardId) {
        // If no active input, auto-select first empty slot
        if (!activeCardInput) {
            activeCardInput = findFirstEmptySlot();
            if (!activeCardInput) {
                showError("All card slots are filled");
                return;
            }
            setActiveInput(activeCardInput);
        }

        const input = document.getElementById(activeCardInput);
        if (!input) return;

        // Check if card is already used
        if (usedCards.has(cardId)) {
            showError(`${cardId} is already in use`);
            return;
        }

        input.value = cardId;
        input.classList.add('valid-card');
        input.setAttribute('data-suit', cardId[1].toLowerCase());

        renderVisualCard(input);

        usedCards.add(cardId);
        updateCardGrid();

        updateBoardCardStates();

        const nextInput = getNextEmptySlot(activeCardInput);
        if (nextInput) {
            setActiveInput(nextInput);
        } else {
            setActiveInput(null);
        }

        setTimeout(checkAndCalculate, 100);
    }

    function updateCardGrid() {
        document.querySelectorAll('.deck-card').forEach(cardBtn => {
            const cardId = cardBtn.dataset.card;
            if (usedCards.has(cardId)) {
                cardBtn.classList.add('card-used');
            } else {
                cardBtn.classList.remove('card-used');
            }
        });
    }

    function setActiveInput(inputId) {
        document.querySelectorAll('.card-input').forEach(inp => {
            inp.classList.remove('active-target');
        });

        activeCardInput = inputId;

        if (inputId) {
            const input = document.getElementById(inputId);
            if (input && !input.disabled) {
                input.classList.add('active-target');
                input.focus();
            }
        }
    }

    function findFirstEmptySlot() {
        for (let i = 0; i < numPlayers; i++) {
            const c1 = document.getElementById(`p${i}-c1`);
            const c2 = document.getElementById(`p${i}-c2`);
            if (c1 && !c1.classList.contains('valid-card')) return c1.id;
            if (c2 && !c2.classList.contains('valid-card')) return c2.id;
        }

        for (let i = 1; i <= 5; i++) {
            const boardCard = document.getElementById(`board-${i}`);
            if (boardCard && !boardCard.classList.contains('valid-card') && !boardCard.disabled) {
                return boardCard.id;
            }
        }

        return null;
    }

    function getNextEmptySlot(currentId) {
        const allSlots = [];

        for (let i = 0; i < numPlayers; i++) {
            allSlots.push(`p${i}-c1`);
            allSlots.push(`p${i}-c2`);
        }
        for (let i = 1; i <= 5; i++) {
            allSlots.push(`board-${i}`);
        }

        const currentIndex = allSlots.indexOf(currentId);
        if (currentIndex === -1) return findFirstEmptySlot();

        for (let i = currentIndex + 1; i < allSlots.length; i++) {
            const slotId = allSlots[i];
            const input = document.getElementById(slotId);
            if (input && !input.classList.contains('valid-card') && !input.disabled) {
                return slotId;
            }
        }

        return null;
    }

    initCardPicker();

    function renderVisualCard(input) {
        const wrapper = input.closest('.card-wrapper');
        if (!wrapper) return;

        const existingCard = wrapper.querySelector('.visual-card');
        const existingRemoveBtn = wrapper.querySelector('.card-remove-btn');
        if (existingCard) existingCard.remove();
        if (existingRemoveBtn) existingRemoveBtn.remove();

        // Only render if input is valid
        if (!input.classList.contains('valid-card')) {
            input.classList.remove('hidden-input');
            return;
        }

        const val = input.value.toUpperCase();
        const rank = val[0];
        const suit = val[1].toLowerCase();
        const suitSymbol = suitSymbols[suit] || suit;
        const colorClass = (suit === 'h' || suit === 'd') ? 'card-red' : 'card-black';

        const visualCard = document.createElement('div');
        visualCard.className = 'visual-card';
        visualCard.innerHTML = `
            <span class="card-rank ${colorClass}">${rank}</span>
            <span class="card-suit-center ${colorClass}">${suitSymbol}</span>
        `;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'card-remove-btn';
        removeBtn.innerHTML = '×';
        removeBtn.type = 'button';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            clearCard(input.id);
        };

        wrapper.appendChild(visualCard);
        wrapper.appendChild(removeBtn);

        input.classList.add('hidden-input');
    }

    function clearCard(inputId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        const cardValue = input.value.toUpperCase();
        if (cardValue && usedCards.has(cardValue)) {
            usedCards.delete(cardValue);
            updateCardGrid();
        }

        input.value = '';
        input.classList.remove('valid-card', 'hidden-input');
        input.removeAttribute('data-suit');

        const wrapper = input.closest('.card-wrapper');
        if (wrapper) {
            const visualCard = wrapper.querySelector('.visual-card');
            const removeBtn = wrapper.querySelector('.card-remove-btn');
            if (visualCard) visualCard.remove();
            if (removeBtn) removeBtn.remove();
        }

        setActiveInput(inputId);

        setTimeout(checkAndCalculate, 100);
    }

    const positionMaps = {
        2: ['pos-bottom', 'pos-top'],
        3: ['pos-bottom', 'pos-top-left', 'pos-top-right'],
        4: ['pos-bottom', 'pos-left', 'pos-top', 'pos-right'],
        5: ['pos-bottom', 'pos-bottom-left', 'pos-top-left', 'pos-top-right', 'pos-bottom-right'],
        6: ['pos-bottom', 'pos-bottom-left', 'pos-top-left', 'pos-top', 'pos-top-right', 'pos-bottom-right']
    };

    renderPlayers(numPlayers);

    setTimeout(() => updateBoardCardStates(), 0);

    playerSelect.addEventListener('change', (e) => {
        numPlayers = parseInt(e.target.value);
        renderPlayers(numPlayers);

        document.querySelectorAll('.board-input').forEach(inp => {
            inp.value = '';
            inp.classList.remove('valid-card', 'hidden-input');
            inp.removeAttribute('data-suit');
            inp.style.borderColor = '';
            inp.style.background = '';
            inp.disabled = false;
            inp.classList.remove('disabled-input');
        });
        document.querySelectorAll('.board-area .visual-card').forEach(el => el.remove());
        document.querySelectorAll('.board-area .card-remove-btn').forEach(el => el.remove());

        // Reset card picker
        usedCards.clear();
        updateCardGrid();

        setTimeout(() => updateBoardCardStates(), 0);

        resetStats();
        // we reset everything when the player count switches
    });

    resetBtn.addEventListener('click', () => {
        document.querySelectorAll('.card-input').forEach(inp => {
            inp.value = '';
            inp.classList.remove('valid-card', 'hidden-input', 'active-target');
            inp.removeAttribute('data-suit');
            inp.disabled = false;
            inp.classList.remove('disabled-input');
            // Clear error styling
            inp.style.borderColor = '';
            inp.style.background = '';
        });
        document.querySelectorAll('.visual-card').forEach(el => el.remove());
        document.querySelectorAll('.card-remove-btn').forEach(el => el.remove());
        document.querySelectorAll('.fold-btn').forEach(btn => {
            btn.classList.remove('active');
            btn.disabled = false;
            btn.closest('.player-seat').classList.remove('folded');
        });

        // Clear card picker
        usedCards.clear();
        updateCardGrid();
        setActiveInput('p0-c1'); // Set first player's first card as active

        // Hide error toast
        showError(null);

        // Reset board card states
        setTimeout(() => updateBoardCardStates(), 0);

        resetStats();
    });

    document.body.addEventListener('input', (e) => {
        if (e.target.classList.contains('card-input')) {
            const val = e.target.value;
            if (val.length === 2) {
                formatCardInput(e.target);

                // Check if card is valid before proceeding
                const isValid = e.target.classList.contains('valid-card');

                if (!isValid) {
                    // Show error styling - keep focus here
                    e.target.style.borderColor = 'var(--accent-red)';
                    e.target.style.background = 'rgba(166, 61, 79, 0.2)';
                    showError(`Invalid card: "${val}". Use format like AS, KH, TD, 2C`);
                    return;
                }

                // Check for duplicate cards
                const currentCard = val.toUpperCase();
                const currentInputId = e.target.id;
                let isDuplicate = false;
                let duplicateLocation = '';

                // Check all player hole cards
                for (let i = 0; i < numPlayers; i++) {
                    const c1 = document.getElementById(`p${i}-c1`);
                    const c2 = document.getElementById(`p${i}-c2`);

                    if (c1 && c1.id !== currentInputId && c1.value.toUpperCase() === currentCard) {
                        isDuplicate = true;
                        duplicateLocation = `Player ${i + 1}`;
                        break;
                    }
                    if (c2 && c2.id !== currentInputId && c2.value.toUpperCase() === currentCard) {
                        isDuplicate = true;
                        duplicateLocation = `Player ${i + 1}`;
                        break;
                    }
                }

                // Check board cards
                if (!isDuplicate) {
                    for (let i = 1; i <= 5; i++) {
                        const boardCard = document.getElementById(`board-${i}`);
                        if (boardCard && boardCard.id !== currentInputId && boardCard.value.toUpperCase() === currentCard) {
                            isDuplicate = true;
                            duplicateLocation = 'Board';
                            break;
                        }
                    }
                }

                if (isDuplicate) {
                    // Clear the invalid input
                    e.target.value = '';
                    e.target.classList.remove('valid-card');
                    e.target.removeAttribute('data-suit');
                    renderVisualCard(e.target);

                    // Show error styling
                    e.target.style.borderColor = 'var(--accent-red)';
                    e.target.style.background = 'rgba(166, 61, 79, 0.2)';

                    // Custom message for board vs player duplicates
                    const errorMsg = duplicateLocation === 'Board' ? `${currentCard} is already on the board` : `Duplicate card: ${currentCard} already used by ${duplicateLocation}`;
                    showError(errorMsg);
                    return;
                }

                e.target.style.borderColor = '';
                e.target.style.background = '';

                // Update card picker when typing
                usedCards.add(currentCard);
                updateCardGrid();

                updateBoardCardStates();

                // Auto-focus next input (only if valid and not disabled)
                const currentId = e.target.id;
                let nextInput = null;

                // If this is first card (c1), focus second card (c2)
                if (currentId.includes('-c1')) {
                    const playerId = currentId.replace('-c1', '');
                    nextInput = document.getElementById(`${playerId}-c2`);
                }
                // If this is second card (c2), focus next player's first card
                else if (currentId.includes('-c2')) {
                    const match = currentId.match(/p(\d+)-c2/);
                    if (match) {
                        const currentPlayer = parseInt(match[1]);
                        const nextPlayer = currentPlayer + 1;
                        if (nextPlayer < numPlayers) {
                            nextInput = document.getElementById(`p${nextPlayer}-c1`);
                        } else {
                            // Last player done, focus first board card
                            nextInput = document.getElementById('board-1');
                        }
                    }
                }
                // Board card progression
                else if (currentId.startsWith('board-')) {
                    const boardNum = parseInt(currentId.split('-')[1]);
                    if (boardNum < 5) {
                        nextInput = document.getElementById(`board-${boardNum + 1}`);
                    }
                }

                if (nextInput && !nextInput.disabled) {
                    nextInput.focus();
                }

                // Auto-calculate when ready
                setTimeout(checkAndCalculate, 100);
            } else {
                e.target.style.background = '';
                e.target.style.color = '';
                e.target.style.borderColor = '';
            }
        }
    });

    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

        document.getElementById(tabId).classList.add('active');
        const btns = document.querySelectorAll('.nav-btn');
        if (tabId === 'live-odds') btns[0].classList.add('active'); else btns[1].classList.add('active');
    }

    window.switchTab = switchTab;

    window.toggleFold = (index) => {
        const seat = document.getElementById(`seat-${index}`);
        const btn = seat.querySelector('.fold-btn');
        const isFolded = seat.classList.contains('folded');

        // Only allow folding, not unfolding
        if (isFolded) {
            console.log(`Player ${index + 1} already folded`);
            return;
        }

        // Count active (non-folded) players
        const activePlayers = document.querySelectorAll('.player-seat:not(.folded)').length;

        // Don't allow folding the last player
        if (activePlayers <= 1) {
            showError("Cannot fold: only 1 player remaining");
            return;
        }

        // Fold the player
        seat.classList.add('folded');
        btn.classList.add('active');
        btn.disabled = true;

        console.log(`Player ${index + 1} folded`);

        checkAndCalculate();
    };

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
                    <div class="card-wrapper">
                        <input type="text" class="card-input p-card" id="p${i}-c1" maxlength="2" placeholder="C1">
                    </div>
                    <div class="card-wrapper">
                        <input type="text" class="card-input p-card" id="p${i}-c2" maxlength="2" placeholder="C2">
                    </div>
                </div>
            `;
            playersContainer.appendChild(seat);
        }
    }


    function isBoardStateValid() {
        const flop1 = document.getElementById('board-1');
        const flop2 = document.getElementById('board-2');
        const flop3 = document.getElementById('board-3');
        const turn = document.getElementById('board-4');
        const river = document.getElementById('board-5');

        const flop1Valid = flop1.classList.contains('valid-card');
        const flop2Valid = flop2.classList.contains('valid-card');
        const flop3Valid = flop3.classList.contains('valid-card');
        const turnValid = turn.classList.contains('valid-card');
        const riverValid = river.classList.contains('valid-card');

        // Count filled cards
        let count = 0;
        if (flop1Valid) count++;
        if (flop2Valid) count++;
        if (flop3Valid) count++;
        if (turnValid) count++;
        if (riverValid) count++;

        // Valid: 0 cards (preflop)
        if (count === 0) return true;

        // Valid: exactly 3 cards (must be complete flop)
        if (count === 3) {
            return flop1Valid && flop2Valid && flop3Valid;
        }

        // Valid: exactly 4 cards (must be flop + turn)
        if (count === 4) {
            return flop1Valid && flop2Valid && flop3Valid && turnValid;
        }

        // Valid: exactly 5 cards (must be all streets)
        if (count === 5) {
            return flop1Valid && flop2Valid && flop3Valid && turnValid && riverValid;
        }

        // Invalid: 1, 2, or any incomplete sequence
        return false;
    }


    function checkAndCalculate() {
        console.log('=== checkAndCalculate called ===');

        // Check if all player cards are filled
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

        updateBoardCardStates();

        // Only calculate if players complete AND board valid
        const boardValid = isBoardStateValid();

        if (allPlayerCardsFilled && boardValid) {
            console.log('Valid state - calculating equity');
            calculateEquity();
        } else {
            console.log('Invalid state - skipping calculation');
        }
    }

    function updateBoardCardStates() {
        // Check flop completion (all 3 cards valid)
        const flop1 = document.getElementById('board-1');
        const flop2 = document.getElementById('board-2');
        const flop3 = document.getElementById('board-3');
        const turn = document.getElementById('board-4');
        const river = document.getElementById('board-5');

        const flopComplete = flop1.classList.contains('valid-card') && flop2.classList.contains('valid-card') && flop3.classList.contains('valid-card');

        const turnValid = turn.classList.contains('valid-card');

        // Disable turn until flop is complete
        if (!flopComplete) {
            turn.disabled = true;
            turn.classList.add('disabled-input');
            if (turn.value) {
                clearCard('board-4');
            }
        } else {
            turn.disabled = false;
            turn.classList.remove('disabled-input');
            turn.placeholder = 'Turn';
        }

        // Disable river until turn is valid
        if (!flopComplete || !turnValid) {
            river.disabled = true;
            river.classList.add('disabled-input');
            if (river.value) {
                clearCard('board-5');
            }
        } else {
            river.disabled = false;
            river.classList.remove('disabled-input');
            river.placeholder = 'River';
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

        renderVisualCard(input);
    }

    async function calculateEquity() {
        console.log('=== calculateEquity started ===');
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
            num_players: numPlayers, hands: hands, board: boardInputs, folded: folded
        };

        try {
            const res = await fetch('/calculate', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
            });

            console.log('Response status:', res.status);
            const data = await res.json();
            console.log('Response data:', data);

            if (data.error) {
                showError(data.error);
                if (data.player) highlightError(data.player);
            } else if (data.status === 'success') {
                updateUI(data);
            }

        } catch (e) {
            console.error('Error in calculateEquity:', e);
            showError("Network or Server Error");
        }
    }

    function updateUI(data) {
        // Update Street
        document.getElementById('current-street-display').innerText = `Street: ${data.street.charAt(0).toUpperCase() + data.street.slice(1)}`;

        // Update Stats
        const splitProb = (data.split_prob * 100).toFixed(1);
        const potStats = document.getElementById('pot-stats');
        document.getElementById('split-prob').innerText = splitProb + '%';
        if (parseFloat(splitProb) > 1.0) potStats.style.display = 'block'; else potStats.style.display = 'none';

        // Build sorted equity list
        const players = [];
        for (let i = 0; i < numPlayers; i++) {
            const eq = parseFloat((data.equities[i.toString()] * 100).toFixed(1));
            players.push({index: i, equity: eq});
        }
        players.sort((a, b) => b.equity - a.equity);

        // Update equity table
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
            if (eq >= winningEquity - 0.1 && eq > 0) {
                seat.classList.add('winner');
            } else {
                seat.classList.remove('winner');
            }
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

});