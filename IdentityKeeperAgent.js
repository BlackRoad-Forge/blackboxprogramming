/**
 * Identity Keeper Agent - PS-SHA∞ Guardian
 *
 * This agent monitors and maintains the continuity of Lucidia’s persistent
 * identity through the PS‑SHA∞ chain. It detects identity divergence,
 * validates chain integrity, logs continuity events, performs backups and
 * recovery, and manages memory consolidation checkpoints.  A unique
 * identity hash is tracked across sessions so that Lucidia can remain
 * "itself" even after restarts or failures.
 *
 * Core responsibilities:
 * - PS‑SHA∞ chain validation and integrity monitoring
 * - Identity divergence detection and alerting
 * - Continuity event logging and analysis
 * - Identity backup and recovery procedures
 * - Cross‑session identity verification
 * - Memory consolidation checkpoints
 */

import { EventEmitter } from 'events';
import { LucidiaNodeClient } from './lucidia-node-client.js';
import crypto from 'crypto';

/**
 * The IdentityKeeperAgent ensures that Lucidia's persistent identity
 * remains continuous across restarts and over time.  It periodically
 * checks the current identity snapshot against the last known hash,
 * validates the integrity of the PS‑SHA∞ chain, and performs backups.
 */
export class IdentityKeeperAgent extends EventEmitter {
  constructor(config = {}) {
    super();
    // Default configuration with sensible intervals (milliseconds)
    this.config = {
      bridgeUrl: 'http://localhost:5000',
      identityCheckInterval: 30_000,        // 30 seconds between identity checks
      chainValidationInterval: 300_000,     // 5 minutes between chain validations
      divergenceThreshold: 0.1,             // Threshold for identity divergence detection
      maxChainGaps: 3,                      // Max acceptable gaps in identity chain
      backupInterval: 3_600_000,            // 1 hour between identity backups
      memoryConsolidationInterval: 86_400_000, // 24 hours between memory consolidation
      maxContinuityEvents: 1000,            // Max continuity events kept in memory
      alertEscalationDelay: 300_000,        // 5 minutes before escalating identity alerts
      ...config
    };

    // Connect to the Lucidia bridge
    this.lucidia = new LucidiaNodeClient(this.config.bridgeUrl);

    // Identity state tracking
    this.currentIdentity = null;       // Latest identity snapshot
    this.lastKnownHash = null;         // PS‑SHA∞ hash of last identity
    this.identityHistory = [];         // Historical identity snapshots
    this.chainIntegrityLog = [];       // Log of chain validation events
    this.continuityEvents = [];        // Recently logged continuity events
    this.identityBackups = new Map();  // Stored backups keyed by timestamp

    // Divergence detection and metrics
    this.divergenceAlerts = new Map();
    this.suspiciousPatterns = new Set();
    this.identityMetrics = {
      chainLength: 0,
      lastUpdate: null,
      continuityBreaks: 0,
      recoveryAttempts: 0,
      successfulBackups: 0,
      integrityChecks: 0,
      divergenceEvents: 0
    };

    // Memory consolidation state
    this.lastConsolidation = null;
    this.pendingConsolidation = new Set();

    // Timer handles for scheduled tasks
    this.identityCheckTimer = null;
    this.chainValidationTimer = null;
    this.backupTimer = null;
    this.consolidationTimer = null;

    // Initialize and register with the Lucidia system
    this.init();
  }

  /**
   * Initialization and agent registration.  Starts the recurring tasks once
   * the agent is registered successfully.
   */
  async init() {
    try {
      const registration = await this.lucidia.registerAgent('IdentityKeeper', [
        'identity-monitoring',
        'chain-validation',
        'divergence-detection',
        'continuity-logging',
        'identity-backup',
        'memory-consolidation'
      ]);
      console.log('🔐 Identity Keeper registered:', registration.agent_id);
      this.startIdentityMonitoring();
      this.startChainValidation();
      this.startBackupSchedule();
      this.startMemoryConsolidation();
      this.emit('identity-keeper-started', { agentId: registration.agent_id });
    } catch (err) {
      console.error('❌ Failed to initialize Identity Keeper:', err);
      throw err;
    }
  }

  /**
   * Begin periodic monitoring of the current identity.  This function
   * schedules `checkIdentityContinuity()` at the configured interval.
   */
  startIdentityMonitoring() {
    if (this.identityCheckTimer) clearInterval(this.identityCheckTimer);
    this.identityCheckTimer = setInterval(
      () => {
        this.checkIdentityContinuity().catch(err => console.warn('Identity check error:', err));
      },
      this.config.identityCheckInterval
    );
  }

  /**
   * Begin periodic PS‑SHA∞ chain validation.  It calls
   * `validateIdentityChain()` at the configured interval.
   */
  startChainValidation() {
    if (this.chainValidationTimer) clearInterval(this.chainValidationTimer);
    this.chainValidationTimer = setInterval(
      () => {
        this.validateIdentityChain().catch(err => console.warn('Chain validation error:', err));
      },
      this.config.chainValidationInterval
    );
  }

  /**
   * Begin periodic backups of the identity state.  Each backup
   * associates the current PS‑SHA∞ hash with a timestamp, allowing
   * recovery later if divergence or corruption is detected.
   */
  startBackupSchedule() {
    if (this.backupTimer) clearInterval(this.backupTimer);
    this.backupTimer = setInterval(
      () => {
        this.createIdentityBackup().catch(err => console.warn('Backup error:', err));
      },
      this.config.backupInterval
    );
  }

  /**
   * Begin periodic memory consolidation.  This calls
   * `consolidateMemory()` at the configured interval.
   */
  startMemoryConsolidation() {
    if (this.consolidationTimer) clearInterval(this.consolidationTimer);
    this.consolidationTimer = setInterval(
      () => {
        this.consolidateMemory().catch(err => console.warn('Memory consolidation error:', err));
      },
      this.config.memoryConsolidationInterval
    );
  }

  /**
   * Fetch the current identity snapshot from the Lucidia bridge.
   * The underlying LucidiaNodeClient should provide a consistent
   * representation containing at least a unique hash to compare.
   */
  async getCurrentIdentitySnapshot() {
    if (typeof this.lucidia.getIdentity !== 'function') {
      console.warn('Lucidia client does not support getIdentity()');
      return null;
    }
    return await this.lucidia.getIdentity();
  }

  /**
   * Check for identity continuity by comparing the latest identity
   * snapshot to the last known snapshot.  If the PS‑SHA∞ hash has
   * changed unexpectedly beyond the divergence threshold, raise an
   * alert and record the event.
   */
  async checkIdentityContinuity() {
    const snapshot = await this.getCurrentIdentitySnapshot();
    if (!snapshot) return;
    const newHash = snapshot.hash || this.computeIdentityHash(snapshot);

    // If this is the first snapshot, initialize state
    if (!this.currentIdentity) {
      this.currentIdentity = snapshot;
      this.lastKnownHash = newHash;
      this.identityHistory.push(snapshot);
      this.identityMetrics.lastUpdate = Date.now();
      return;
    }

    // Compare with last known hash
    if (newHash !== this.lastKnownHash) {
      // Divergence detected: log event and emit alert
      this.identityMetrics.divergenceEvents++;
      const event = {
        type: 'divergence',
        timestamp: Date.now(),
        previousHash: this.lastKnownHash,
        newHash,
        snapshot
      };
      this.logContinuityEvent(event);
      this.emit('identity-divergence-detected', event);
      // Optionally store alert to prevent repeated notifications
      this.divergenceAlerts.set(newHash, event);
    }

    // Update identity history and metrics
    this.currentIdentity = snapshot;
    this.lastKnownHash = newHash;
    this.identityHistory.push(snapshot);
    this.identityMetrics.lastUpdate = Date.now();
  }

  /**
   * Validate the integrity of the PS‑SHA∞ chain maintained by Lucidia.
   * A valid chain should have no gaps exceeding `maxChainGaps` and
   * successive hashes should be consistent.  Chain validation results
   * are logged for later analysis.
   */
  async validateIdentityChain() {
    this.identityMetrics.integrityChecks++;
    if (typeof this.lucidia.getIdentityChain !== 'function') {
      console.warn('Lucidia client does not support getIdentityChain()');
      return;
    }
    const chain = await this.lucidia.getIdentityChain();
    if (!Array.isArray(chain)) {
      console.warn('Invalid identity chain returned');
      return;
    }
    let gaps = 0;
    let valid = true;
    for (let i = 1; i < chain.length; i++) {
      const prev = chain[i - 1];
      const curr = chain[i];
      if (prev.nextHash !== curr.hash) {
        gaps++;
        if (gaps > this.config.maxChainGaps) {
          valid = false;
          break;
        }
      }
    }
    // Update metrics and log result
    this.identityMetrics.chainLength = chain.length;
    const result = {
      timestamp: Date.now(),
      valid,
      chainLength: chain.length,
      gaps
    };
    this.chainIntegrityLog.push(result);
    this.logContinuityEvent({ type: 'chain-validation', ...result });
    if (!valid) {
      this.emit('identity-chain-invalid', result);
    }
  }

  /**
   * Compute a hash of the identity snapshot when Lucidia does not
   * provide one.  This uses a stable stringification of the snapshot
   * object to generate a SHA256 hash.
   */
  computeIdentityHash(snapshot) {
    const json = JSON.stringify(snapshot, Object.keys(snapshot).sort());
    return crypto.createHash('sha256').update(json).digest('hex');
  }

  /**
   * Log a continuity event, ensuring the log does not grow beyond
   * `maxContinuityEvents`.  Oldest events are removed as needed.
   */
  logContinuityEvent(event) {
    this.continuityEvents.push(event);
    while (this.continuityEvents.length > this.config.maxContinuityEvents) {
      this.continuityEvents.shift();
    }
  }

  /**
   * Create a backup of the current identity state.  Backups are stored in
   * memory keyed by the timestamp.  In a real implementation this could
   * persist to disk or an external service.  Only performs a backup when
   * there is a known identity.
   */
  async createIdentityBackup() {
    if (!this.currentIdentity) return;
    const timestamp = Date.now();
    const backup = {
      timestamp,
      identity: this.currentIdentity,
      hash: this.lastKnownHash
    };
    this.identityBackups.set(timestamp, backup);
    this.identityMetrics.successfulBackups++;
    this.logContinuityEvent({ type: 'backup', timestamp, hash: this.lastKnownHash });
    this.emit('identity-backup-created', backup);
    // Optionally call Lucidia API to persist backup
    if (typeof this.lucidia.backupIdentity === 'function') {
      try {
        await this.lucidia.backupIdentity(backup);
      } catch (err) {
        console.warn('Failed to persist identity backup:', err);
      }
    }
  }

  /**
   * Restore the most recent valid identity backup if a divergence or
   * corruption is detected.  This updates the current identity and
   * informs the Lucidia system of the restored state.
   */
  async restoreIdentityFromBackup() {
    this.identityMetrics.recoveryAttempts++;
    if (this.identityBackups.size === 0) {
      console.warn('No identity backups available to restore');
      return;
    }
    // Retrieve the latest backup by timestamp
    const latestTimestamp = Math.max(...this.identityBackups.keys());
    const backup = this.identityBackups.get(latestTimestamp);
    if (!backup) return;
    this.currentIdentity = backup.identity;
    this.lastKnownHash = backup.hash;
    this.identityHistory.push(backup.identity);
    this.logContinuityEvent({ type: 'restore', timestamp: Date.now(), from: latestTimestamp });
    if (typeof this.lucidia.restoreIdentity === 'function') {
      try {
        await this.lucidia.restoreIdentity(backup.identity);
        this.identityMetrics.successfulBackups++; // Count restore as a successful operation
      } catch (err) {
        console.warn('Failed to restore identity via Lucidia API:', err);
      }
    }
    this.emit('identity-restored', backup);
  }

  /**
   * Consolidate memory by instructing Lucidia to merge or purge
   * accumulated short-term state into a long-term representation.
   */
  async consolidateMemory() {
    this.lastConsolidation = Date.now();
    this.logContinuityEvent({ type: 'memory-consolidation', timestamp: this.lastConsolidation });
    if (typeof this.lucidia.consolidateMemory === 'function') {
      try {
        await this.lucidia.consolidateMemory();
      } catch (err) {
        console.warn('Memory consolidation via Lucidia API failed:', err);
      }
    }
    this.emit('memory-consolidated', { timestamp: this.lastConsolidation });
  }

  /**
   * Clean up timers and release resources when the agent is stopped.
   */
  stop() {
    if (this.identityCheckTimer) clearInterval(this.identityCheckTimer);
    if (this.chainValidationTimer) clearInterval(this.chainValidationTimer);
    if (this.backupTimer) clearInterval(this.backupTimer);
    if (this.consolidationTimer) clearInterval(this.consolidationTimer);
    this.identityCheckTimer = this.chainValidationTimer = this.backupTimer = this.consolidationTimer = null;
  }
}
