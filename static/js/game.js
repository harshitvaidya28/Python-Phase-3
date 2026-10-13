/**
 * Rock, Paper, Scissors — Phase 3 Arcade Edition
 * Client-side Game Controller, Web Audio Synthesizer & Particle Confetti
 */

// ==========================================
// 1. Audio Synthesizer (Native Web Audio API)
// ==========================================
class WebSoundManager {
  constructor() {
    this.enabled = true;
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playTone(freq, durationMs, type = 'sine', gainVal = 0.15) {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + (durationMs / 1000));

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + (durationMs / 1000));
    } catch (e) {
      console.warn("Audio play error", e);
    }
  }

  playClick() {
    this.playTone(800, 35, 'sine', 0.1);
  }

  playCountdownTick() {
    this.playTone(650, 90, 'triangle', 0.2);
  }

  playCountdownGo() {
    this.playTone(980, 160, 'square', 0.15);
  }

  playVictory() {
    if (!this.enabled) return;
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 220, 'triangle', 0.22);
      }, idx * 110);
    });
  }

  playDefeat() {
    if (!this.enabled) return;
    const notes = [440, 349.23, 261.63];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 260, 'sawtooth', 0.12);
      }, idx * 140);
    });
  }

  playDraw() {
    if (!this.enabled) return;
    this.playTone(500, 140, 'sine', 0.15);
    setTimeout(() => this.playTone(500, 180, 'sine', 0.15), 150);
  }

  playAchievement() {
    if (!this.enabled) return;
    const notes = [587.33, 739.99, 880.00, 1174.66];
    notes.forEach((freq, idx) => {
      setTimeout(() => {
        this.playTone(freq, 200, 'sine', 0.25);
      }, idx * 90);
    });
  }
}

// ==========================================
// 2. Confetti Particle Physics System
// ==========================================
class ConfettiEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.particles = [];
    this.animationFrame = null;
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  burst(count = 90) {
    if (!this.canvas || !this.ctx) return;
    this.resize();
    const colors = ['#00F5FF', '#FF007F', '#00FF9D', '#FFD700', '#8B5CF6', '#FFFFFF'];
    const originX = this.canvas.width / 2;
    const originY = this.canvas.height * 0.45;

    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 12 + 5;
      this.particles.push({
        x: originX,
        y: originY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - (Math.random() * 5 + 3),
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        gravity: 0.38,
        friction: 0.97,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 12,
        life: Math.random() * 40 + 50,
        maxLife: 90,
      });
    }

    if (!this.animationFrame) {
      this.loop();
    }
  }

  loop() {
    if (!this.ctx) return;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.vx *= p.friction;
      p.rotation += p.rotationSpeed;
      p.life--;

      this.ctx.save();
      this.ctx.translate(p.x, p.y);
      this.ctx.rotate((p.rotation * Math.PI) / 180);
      this.ctx.fillStyle = p.color;
      this.ctx.globalAlpha = Math.max(0, p.life / p.maxLife);
      this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
      this.ctx.restore();

      if (p.life <= 0 || p.y > this.canvas.height + 20) {
        this.particles.splice(i, 1);
      }
    }

    if (this.particles.length > 0) {
      this.animationFrame = requestAnimationFrame(() => this.loop());
    } else {
      this.animationFrame = null;
    }
  }
}

// ==========================================
// 3. Main Game Controller
// ==========================================
class ArcadeGameController {
  constructor() {
    this.sound = new WebSoundManager();
    this.confetti = new ConfettiEngine('confetti-canvas');
    this.currentMode = "Quick Play";
    this.isClashing = false;

    this.cacheDom();
    this.bindEvents();
    this.loadInitialState();
  }

  cacheDom() {
    // Nav elements
    this.themeToggleBtn = document.getElementById('theme-toggle-btn');
    this.themeIcon = document.getElementById('theme-icon');
    this.soundToggleBtn = document.getElementById('sound-toggle-btn');
    this.soundIcon = document.getElementById('sound-icon');
    this.playerNameDisplay = document.getElementById('player-name-display');
    this.cardPlayerName = document.getElementById('card-player-name');
    this.playerProfileBtn = document.getElementById('player-profile-btn');

    // Mode elements
    this.modePills = document.querySelectorAll('.mode-pill');
    this.matchTracker = document.getElementById('match-tracker');
    this.matchRoundIndicator = document.getElementById('match-round-indicator');
    this.matchTargetIndicator = document.getElementById('match-target-indicator');
    this.trackerPlayerScore = document.getElementById('tracker-player-score');
    this.trackerComputerScore = document.getElementById('tracker-computer-score');
    this.playerBarFill = document.getElementById('player-bar-fill');
    this.computerBarFill = document.getElementById('computer-bar-fill');

    // Arena elements
    this.playerPreview = document.getElementById('player-preview');
    this.playerPreviewLabel = document.getElementById('player-preview-label');
    this.computerPreview = document.getElementById('computer-preview');
    this.computerPreviewLabel = document.getElementById('computer-preview-label');
    this.countdownCircle = document.getElementById('countdown-circle');
    this.countdownText = document.getElementById('countdown-text');
    this.statusHeadline = document.getElementById('status-headline');
    this.statusSubtext = document.getElementById('status-subtext');
    this.resetMatchBtn = document.getElementById('reset-match-btn');
    this.weaponButtons = document.querySelectorAll('.weapon-btn');
    this.aiWinCount = document.getElementById('ai-win-count');
    this.aiStatusNote = document.getElementById('ai-status-note');

    // Stats elements
    this.statTotalRounds = document.getElementById('stat-total-rounds');
    this.statWinRate = document.getElementById('stat-win-rate');
    this.statPlayerWins = document.getElementById('stat-player-wins');
    this.statComputerWins = document.getElementById('stat-computer-wins');
    this.statDraws = document.getElementById('stat-draws');
    this.statCurrentStreak = document.getElementById('stat-current-streak');
    this.statLongestStreak = document.getElementById('stat-longest-streak');

    // Achievements & History elements
    this.achievementsGrid = document.getElementById('achievements-grid');
    this.toastContainer = document.getElementById('toast-container');
    this.tabHistoryBtn = document.getElementById('tab-history-btn');
    this.tabLeaderboardBtn = document.getElementById('tab-leaderboard-btn');
    this.tabHistoryContent = document.getElementById('tab-history-content');
    this.tabLeaderboardContent = document.getElementById('tab-leaderboard-content');
    this.historyTbody = document.getElementById('history-tbody');
    this.leaderboardTbody = document.getElementById('leaderboard-tbody');
    this.clearDataBtn = document.getElementById('clear-data-btn');

    // Modals
    this.matchModal = document.getElementById('match-modal');
    this.modalTitle = document.getElementById('modal-title');
    this.modalMessage = document.getElementById('modal-message');
    this.modalTrophy = document.getElementById('modal-trophy-icon');
    this.modalPlayerScore = document.getElementById('modal-player-score');
    this.modalComputerScore = document.getElementById('modal-computer-score');
    this.modalRematchBtn = document.getElementById('modal-rematch-btn');
    this.modalCloseBtn = document.getElementById('modal-close-btn');

    this.profileModal = document.getElementById('profile-modal');
    this.playerNameInput = document.getElementById('player-name-input');
    this.savePlayerNameBtn = document.getElementById('save-player-name-btn');
    this.closeProfileModalBtn = document.getElementById('close-profile-modal-btn');

    this.confirmModal = document.getElementById('confirm-modal');
    this.confirmClearBtn = document.getElementById('confirm-clear-btn');
    this.cancelClearBtn = document.getElementById('cancel-clear-btn');
  }

  bindEvents() {
    // Theme toggle
    this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());

    // Sound toggle
    this.soundToggleBtn.addEventListener('click', () => this.toggleSound());

    // Mode selection
    this.modePills.forEach(pill => {
      pill.addEventListener('click', () => {
        const mode = pill.dataset.mode;
        this.selectMode(mode);
      });
    });

    // Weapon clicks
    this.weaponButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (this.isClashing) return;
        const choice = btn.dataset.choice;
        this.clash(choice);
      });
    });

    // Reset Match
    this.resetMatchBtn.addEventListener('click', () => this.resetMatch());

    // Modals
    this.playerProfileBtn.addEventListener('click', () => {
      this.playerNameInput.value = this.playerNameDisplay.textContent;
      this.profileModal.classList.remove('hidden');
    });
    this.closeProfileModalBtn.addEventListener('click', () => {
      this.profileModal.classList.add('hidden');
    });
    this.savePlayerNameBtn.addEventListener('click', () => this.savePlayerName());

    this.clearDataBtn.addEventListener('click', () => {
      this.confirmModal.classList.remove('hidden');
    });
    this.cancelClearBtn.addEventListener('click', () => {
      this.confirmModal.classList.add('hidden');
    });
    this.confirmClearBtn.addEventListener('click', () => this.executeClearData());

    this.modalRematchBtn.addEventListener('click', () => {
      this.matchModal.classList.add('hidden');
      this.resetMatch();
    });
    this.modalCloseBtn.addEventListener('click', () => {
      this.matchModal.classList.add('hidden');
    });

    // Tabs
    this.tabHistoryBtn.addEventListener('click', () => this.switchTab('history'));
    this.tabLeaderboardBtn.addEventListener('click', () => this.switchTab('leaderboard'));
  }

  async loadInitialState() {
    try {
      const res = await fetch(`/api/state?mode=${encodeURIComponent(this.currentMode)}`);
      const data = await res.json();

      this.applySettings(data.settings);
      this.renderStatistics(data.statistics);
      this.renderAchievements(data.achievements);
      this.renderHistory(data.history);
      this.renderLeaderboard(data.leaderboard);
      this.updateMatchTracker(data.match);
    } catch (e) {
      console.error("Failed to load initial state:", e);
    }
  }

  applySettings(settings) {
    if (!settings) return;
    if (settings.theme) {
      document.documentElement.setAttribute('data-theme', settings.theme);
      this.themeIcon.textContent = settings.theme === 'light' ? '☀️' : '🌙';
    }
    if (typeof settings.sound_enabled === 'boolean') {
      this.sound.enabled = settings.sound_enabled;
      this.soundIcon.textContent = settings.sound_enabled ? '🔊' : '🔇';
    }
    if (settings.player_name) {
      this.playerNameDisplay.textContent = settings.player_name;
      this.cardPlayerName.textContent = settings.player_name;
    }
  }

  toggleTheme() {
    this.sound.playClick();
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    this.themeIcon.textContent = nextTheme === 'light' ? '☀️' : '🌙';

    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ theme: nextTheme })
    }).catch(console.warn);
  }

  toggleSound() {
    this.sound.enabled = !this.sound.enabled;
    this.soundIcon.textContent = this.sound.enabled ? '🔊' : '🔇';
    if (this.sound.enabled) this.sound.playClick();

    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sound_enabled: this.sound.enabled })
    }).catch(console.warn);
  }

  async savePlayerName() {
    const newName = this.playerNameInput.value.trim() || "Player 1";
    this.playerNameDisplay.textContent = newName;
    this.cardPlayerName.textContent = newName;
    this.profileModal.classList.add('hidden');
    this.sound.playClick();

    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: newName })
    });
  }

  selectMode(mode) {
    this.sound.playClick();
    this.currentMode = mode;

    this.modePills.forEach(pill => {
      pill.classList.toggle('active', pill.dataset.mode === mode);
    });

    if (mode === "Quick Play") {
      this.matchTracker.classList.add('hidden');
      this.resetMatchBtn.classList.add('hidden');
    } else {
      this.matchTracker.classList.remove('hidden');
      this.resetMatchBtn.classList.remove('hidden');
      this.matchTargetIndicator.textContent = mode === "Best of 5" ? "First to 3 Wins" : "Endurance (10 Rounds)";
    }

    this.loadInitialState();
  }

  async clash(playerChoice) {
    if (this.isClashing) return;
    this.isClashing = true;
    this.sound.playClick();

    // Visual selection highlight
    this.weaponButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.choice === playerChoice);
    });

    const weaponEmojis = { rock: '✊', paper: '✋', scissors: '✌️' };
    this.playerPreview.textContent = weaponEmojis[playerChoice];
    this.playerPreview.classList.add('bounce');
    this.playerPreviewLabel.textContent = `Locked in: ${playerChoice.toUpperCase()}`;

    // Start 3-2-1 Animated Countdown & Opponent Shuffle
    this.aiStatusNote.textContent = "AI Deciding...";
    const shuffleChoices = ['✊', '✋', '✌️'];
    let shuffleIdx = 0;
    const shuffleInterval = setInterval(() => {
      this.computerPreview.textContent = shuffleChoices[shuffleIdx % 3];
      shuffleIdx++;
    }, 110);

    // Countdown step 3
    this.countdownCircle.classList.add('pulse');
    this.countdownText.textContent = "3";
    this.statusHeadline.textContent = "READY...";
    this.sound.playCountdownTick();

    await this.delay(650);

    // Countdown step 2
    this.countdownText.textContent = "2";
    this.statusHeadline.textContent = "SET...";
    this.sound.playCountdownTick();

    await this.delay(650);

    // Countdown step 1
    this.countdownText.textContent = "1";
    this.statusHeadline.textContent = "CLASH!";
    this.sound.playCountdownTick();

    await this.delay(650);

    // Stop shuffle
    clearInterval(shuffleInterval);

    // Call Backend API
    try {
      const res = await fetch('/api/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_choice: playerChoice,
          mode: this.currentMode
        })
      });
      const data = await res.json();

      this.resolveRound(data, playerChoice);
    } catch (err) {
      console.error("Clash error:", err);
      this.statusHeadline.textContent = "COMMUNICATION ERROR";
      this.isClashing = false;
    }
  }

  resolveRound(data, playerChoice) {
    const outcome = data.round_outcome;
    const result = outcome.result; // 'win', 'lose', 'draw'
    const compChoice = outcome.computer_choice;
    const compMeta = data.computer_meta;

    // Reveal Computer Choice
    this.computerPreview.textContent = compMeta.emoji;
    this.computerPreview.classList.add('bounce');
    this.computerPreviewLabel.textContent = compMeta.label;
    this.aiStatusNote.textContent = "AI Move Revealed";

    this.countdownCircle.classList.remove('pulse');

    // Audio and Visuals based on outcome
    if (result === 'win') {
      this.sound.playCountdownGo();
      setTimeout(() => this.sound.playVictory(), 250);
      this.confetti.burst(80);
      this.countdownText.textContent = "WIN!";
      this.statusHeadline.textContent = "🎉 YOU WON THIS ROUND!";
      this.statusHeadline.style.color = "var(--accent-green)";
    } else if (result === 'lose') {
      this.sound.playDefeat();
      this.countdownText.textContent = "LOSS";
      this.statusHeadline.textContent = "💀 COMPUTER WON THIS ROUND!";
      this.statusHeadline.style.color = "var(--accent-pink)";
    } else {
      this.sound.playDraw();
      this.countdownText.textContent = "DRAW";
      this.statusHeadline.textContent = "🤝 IT'S A STALEMATE DRAW!";
      this.statusHeadline.style.color = "var(--accent-yellow)";
    }

    this.statusSubtext.textContent = outcome.message;

    // Update Statistics & Match Tracker
    this.renderStatistics(data.statistics);
    this.updateMatchTracker(outcome);

    // Show Achievement Toast notifications if unlocked
    if (data.newly_unlocked && data.newly_unlocked.length > 0) {
      data.newly_unlocked.forEach(ach => this.showAchievementToast(ach));
      this.refreshAchievements();
    }

    // Append to live history table
    this.prependHistoryRow({
      round: outcome.round_number,
      mode: outcome.mode,
      player_choice: outcome.player_choice,
      computer_choice: outcome.computer_choice,
      result: outcome.result,
      timestamp: "Just now"
    });

    // Check Match Completion (Bo5 / Bo10)
    if (outcome.is_match_over) {
      setTimeout(() => this.showMatchOverModal(outcome), 1200);
    }

    setTimeout(() => {
      this.playerPreview.classList.remove('bounce');
      this.computerPreview.classList.remove('bounce');
      this.isClashing = false;
    }, 1000);
  }

  updateMatchTracker(match) {
    if (!match || this.currentMode === "Quick Play") return;

    this.matchRoundIndicator.textContent = `Round ${match.round_number}`;
    this.trackerPlayerScore.textContent = match.player_score;
    this.trackerComputerScore.textContent = match.computer_score;

    const maxPoints = this.currentMode === "Best of 5" ? 3 : 10;
    const playerPct = Math.min(100, (match.player_score / maxPoints) * 100);
    const computerPct = Math.min(100, (match.computer_score / maxPoints) * 100);

    this.playerBarFill.style.width = `${playerPct}%`;
    this.computerBarFill.style.width = `${computerPct}%`;
  }

  showMatchOverModal(match) {
    this.modalPlayerScore.textContent = match.player_score;
    this.modalComputerScore.textContent = match.computer_score;

    if (match.match_winner === 'player') {
      this.sound.playVictory();
      this.confetti.burst(150);
      this.modalTrophy.textContent = "👑";
      this.modalTitle.textContent = "TOURNAMENT CHAMPION!";
      this.modalMessage.textContent = `Outstanding! You defeated the AI in ${match.mode}!`;
    } else if (match.match_winner === 'computer') {
      this.sound.playDefeat();
      this.modalTrophy.textContent = "💀";
      this.modalTitle.textContent = "MATCH DEFEATED";
      this.modalMessage.textContent = `The AI conquered this ${match.mode} tournament. Seek redemption!`;
    } else {
      this.sound.playDraw();
      this.modalTrophy.textContent = "🤝";
      this.modalTitle.textContent = "HONORABLE TIE";
      this.modalMessage.textContent = `Scores tied after ${match.round_number} rounds. A worthy clash!`;
    }

    this.matchModal.classList.remove('hidden');
    this.loadInitialState(); // Refresh leaderboards
  }

  async resetMatch() {
    this.sound.playClick();
    const res = await fetch('/api/reset-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: this.currentMode })
    });
    const data = await res.json();
    this.updateMatchTracker(data.match);
    this.countdownText.textContent = "VS";
    this.statusHeadline.textContent = "NEW MATCH STARTED";
    this.statusHeadline.style.color = "var(--text-primary)";
    this.statusSubtext.textContent = "Select your weapon to begin the clash";
    this.weaponButtons.forEach(btn => btn.classList.remove('active'));
    this.playerPreview.textContent = "✊";
    this.computerPreview.textContent = "🤖";
    this.playerPreviewLabel.textContent = "Pick Your Weapon";
    this.computerPreviewLabel.textContent = "Waiting for move...";
  }

  renderStatistics(stats) {
    if (!stats) return;
    this.statTotalRounds.textContent = stats.total_rounds || 0;
    this.statWinRate.textContent = `${stats.win_rate || 0.0}%`;
    this.statPlayerWins.textContent = stats.player_wins || 0;
    this.statComputerWins.textContent = stats.computer_wins || 0;
    this.statDraws.textContent = stats.draws || 0;
    this.statCurrentStreak.textContent = stats.current_streak || 0;
    this.statLongestStreak.textContent = stats.longest_streak || 0;
    this.aiWinCount.textContent = stats.computer_wins || 0;
  }

  renderAchievements(achievements) {
    if (!achievements) return;
    this.achievementsGrid.innerHTML = '';

    achievements.forEach(ach => {
      const card = document.createElement('div');
      card.className = `ach-card ${ach.unlocked ? 'unlocked' : 'locked'}`;
      card.innerHTML = `
        <div class="ach-icon-box">${ach.icon}</div>
        <div class="ach-info">
          <h4 class="ach-title">${ach.title}</h4>
          <p class="ach-desc">${ach.desc}</p>
          <span class="ach-badge-tag">${ach.unlocked ? '✨ Unlocked' : '🔒 Locked'}</span>
        </div>
      `;
      this.achievementsGrid.appendChild(card);
    });
  }

  async refreshAchievements() {
    const res = await fetch('/api/state');
    const data = await res.json();
    this.renderAchievements(data.achievements);
  }

  showAchievementToast(ach) {
    this.sound.playAchievement();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <div class="toast-icon">${ach.icon || '🏆'}</div>
      <div class="toast-body">
        <span class="toast-title">Achievement Unlocked!</span>
        <span class="toast-msg">${ach.title}: ${ach.desc}</span>
      </div>
    `;

    this.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slideToastIn 0.3s reverse forwards';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  }

  renderHistory(history) {
    if (!history || history.length === 0) {
      this.historyTbody.innerHTML = `<tr><td colspan="6" class="empty-cell">No rounds logged yet. Clash now!</td></tr>`;
      return;
    }

    this.historyTbody.innerHTML = history.map(item => this.createHistoryRowHtml(item)).join('');
  }

  createHistoryRowHtml(item) {
    const weaponEmojis = { rock: '✊ Rock', paper: '✋ Paper', scissors: '✌️ Scissors' };
    const pEmoji = weaponEmojis[item.player_choice] || item.player_choice;
    const cEmoji = weaponEmojis[item.computer_choice] || item.computer_choice;
    
    let badgeClass = 'badge-draw';
    let badgeText = 'DRAW';
    if (item.result === 'win') {
      badgeClass = 'badge-win';
      badgeText = 'WIN';
    } else if (item.result === 'lose') {
      badgeClass = 'badge-lose';
      badgeText = 'LOSS';
    }

    return `
      <tr>
        <td>#${item.round}</td>
        <td>${item.mode}</td>
        <td><strong>${pEmoji}</strong></td>
        <td>${cEmoji}</td>
        <td><span class="badge ${badgeClass}">${badgeText}</span></td>
        <td>${item.timestamp}</td>
      </tr>
    `;
  }

  prependHistoryRow(item) {
    const empty = this.historyTbody.querySelector('.empty-cell');
    if (empty) empty.parentElement.remove();

    const temp = document.createElement('tbody');
    temp.innerHTML = this.createHistoryRowHtml(item);
    this.historyTbody.insertBefore(temp.firstElementChild, this.historyTbody.firstChild);
  }

  renderLeaderboard(leaderboard) {
    if (!leaderboard || leaderboard.length === 0) {
      this.leaderboardTbody.innerHTML = `<tr><td colspan="6" class="empty-cell">No completed tournament matches yet.</td></tr>`;
      return;
    }

    this.leaderboardTbody.innerHTML = leaderboard.map(entry => {
      let badgeClass = entry.outcome === 'Victory' ? 'badge-win' : (entry.outcome === 'Defeat' ? 'badge-lose' : 'badge-draw');
      return `
        <tr>
          <td>${entry.date}</td>
          <td><strong>${entry.player_name || 'Player 1'}</strong></td>
          <td>${entry.mode}</td>
          <td>${entry.player_score} - ${entry.computer_score}</td>
          <td>${entry.rounds_played}</td>
          <td><span class="badge ${badgeClass}">${entry.outcome.toUpperCase()}</span></td>
        </tr>
      `;
    }).join('');
  }

  switchTab(tab) {
    this.sound.playClick();
    if (tab === 'history') {
      this.tabHistoryBtn.classList.add('active');
      this.tabLeaderboardBtn.classList.remove('active');
      this.tabHistoryContent.classList.add('active');
      this.tabLeaderboardContent.classList.remove('active');
    } else {
      this.tabLeaderboardBtn.classList.add('active');
      this.tabHistoryBtn.classList.remove('active');
      this.tabLeaderboardContent.classList.add('active');
      this.tabHistoryContent.classList.remove('active');
    }
  }

  async executeClearData() {
    this.sound.playClick();
    this.confirmModal.classList.add('hidden');
    await fetch('/api/clear-history', { method: 'POST' });
    this.loadInitialState();
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Bootstrap after DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  window.rpsApp = new ArcadeGameController();
});
