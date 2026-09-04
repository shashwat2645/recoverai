// RecoverAI Interactive Dashboard Engine

const API_BASE = '/api/v1';
let authToken = localStorage.getItem('recoverai_token') || null;
let currentFilter = 'ALL';
let allCases = [];

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await ensureAuthenticated();
    setupEventListeners();
    await refreshDashboard();

    // Auto refresh metrics every 10 seconds
    setInterval(refreshMetrics, 10000);
});

// Authentication Helper
async function ensureAuthenticated() {
    if (!authToken) {
        try {
            // Auto register/login demo merchant for seamless hackathon walkthrough
            const regRes = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'Demo Merchant Store',
                    email: 'merchant@recoverai.demo',
                    password: 'DemoPassword123!',
                    razorpay_key_id: 'rzp_test_buildathon',
                    razorpay_key_secret: 'demo_secret'
                })
            });

            const loginRes = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: 'merchant@recoverai.demo',
                    password: 'DemoPassword123!'
                })
            });

            if (loginRes.ok) {
                const data = await loginRes.json();
                authToken = data.access_token;
                localStorage.setItem('recoverai_token', authToken);
            }
        } catch (err) {
            console.error('Auth initialization error:', err);
        }
    }
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}

// Event Listeners
function setupEventListeners() {
    // Modals
    const modalSimulate = document.getElementById('modalSimulate');
    const modalAudit = document.getElementById('modalAudit');
    const modalPolicies = document.getElementById('modalPolicies');

    document.getElementById('btnSimulateModal').onclick = () => modalSimulate.classList.add('open');
    document.getElementById('btnCloseSimulate').onclick = () => modalSimulate.classList.remove('open');
    document.getElementById('btnCancelSimulate').onclick = () => modalSimulate.classList.remove('open');

    document.getElementById('btnCloseAudit').onclick = () => modalAudit.classList.remove('open');
    document.getElementById('btnOpenPolicies').onclick = () => {
        loadPolicies();
        modalPolicies.classList.add('open');
    };
    document.getElementById('btnClosePolicies').onclick = () => modalPolicies.classList.remove('open');

    // Simulate Form Submission
    document.getElementById('formSimulate').onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
            failure_reason: document.getElementById('simFailureReason').value,
            amount: parseFloat(document.getElementById('simAmount').value),
            currency: document.getElementById('simCurrency').value,
            customer_email: document.getElementById('simCustomerEmail').value,
            customer_phone: document.getElementById('simCustomerPhone').value,
            event_type: 'payment.failed'
        };

        try {
            const res = await fetch(`${API_BASE}/events/simulate`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                showToast('⚡ Payment failure ingested! Risk detected automatically.', 'success');
                modalSimulate.classList.remove('open');
                await refreshDashboard();
            } else {
                showToast('Failed to simulate event', 'error');
            }
        } catch (err) {
            showToast('Error connecting to backend', 'error');
        }
    };

    // Filter Tabs
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.onclick = () => {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFilter = tab.dataset.filter;
            renderCasesTable();
        };
    });

    // Autonomous Recover All
    document.getElementById('btnAutoRecoverAll').onclick = async () => {
        const actionableCases = allCases.filter(c => c.status === 'DETECTED' || c.status === 'ACTION_REQUIRED');
        if (actionableCases.length === 0) {
            showToast('No pending cases require autonomous recovery.', 'info');
            return;
        }

        showToast(`Triggering autonomous recovery on ${actionableCases.length} cases...`, 'info');

        for (const c of actionableCases) {
            if (c.status === 'DETECTED') {
                await fetch(`${API_BASE}/cases/${c.id}/analyze`, { method: 'POST', headers: getAuthHeaders() });
            }
            await fetch(`${API_BASE}/cases/${c.id}/execute`, { method: 'POST', headers: getAuthHeaders() });
        }

        showToast('Autonomous recovery completed successfully!', 'success');
        await refreshDashboard();
    };

    // Add Policy Form
    document.getElementById('formAddPolicy').onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
            title: document.getElementById('policyTitle').value,
            policy_type: document.getElementById('policyType').value,
            content: document.getElementById('policyContent').value
        };

        const res = await fetch(`${API_BASE}/policies`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('Policy indexed into vector store!', 'success');
            document.getElementById('policyTitle').value = '';
            document.getElementById('policyContent').value = '';
            loadPolicies();
        }
    };
}

// Refresh Dashboard Data
async function refreshDashboard() {
    await Promise.all([refreshMetrics(), refreshCases()]);
}

// Refresh Metrics
async function refreshMetrics() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/metrics`, { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('statTotalFailed').innerText = data.total_failed_payments;
            document.getElementById('statRevenueAtRisk').innerText = `₹${data.revenue_at_risk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById('statRecoveredRevenue').innerText = `₹${data.recovered_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
            document.getElementById('statSuccessRate').innerText = `${data.recovery_success_rate_pct}%`;
            document.getElementById('statFalseActions').innerText = data.false_actions_avoided;
            document.getElementById('statActiveCount').innerText = data.active_cases;
        }
    } catch (err) {
        console.error('Error fetching metrics:', err);
    }
}

// Refresh Cases
async function refreshCases() {
    try {
        const res = await fetch(`${API_BASE}/cases`, { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            allCases = data.cases || [];
            renderCasesTable();
        }
    } catch (err) {
        console.error('Error fetching cases:', err);
    }
}

// Render Cases Table
function renderCasesTable() {
    const tbody = document.getElementById('casesTableBody');
    let filtered = allCases;

    if (currentFilter !== 'ALL') {
        filtered = allCases.filter(c => c.status === currentFilter);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="table-empty">No recovery cases found for filter "${currentFilter}". Click "+ Simulate Failure" to inject events.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(c => {
        const statusClass = `badge-${c.status.toLowerCase().replace('_', '')}`;
        const riskClass = c.risk_score >= 0.8 ? 'risk-high' : c.risk_score >= 0.5 ? 'risk-medium' : 'risk-low';

        return `
            <tr>
                <td><code style="font-size:12px; color:var(--text-secondary);">${c.id.substring(0, 8)}...</code></td>
                <td>
                    <div style="font-weight:600;">${c.customer_email}</div>
                    <div style="font-size:12px; color:var(--text-muted);">${new Date(c.created_at).toLocaleTimeString()}</div>
                </td>
                <td style="font-weight:700; font-family:var(--font-heading);">₹${c.amount_at_risk.toFixed(2)}</td>
                <td><span class="risk-pill ${riskClass}">Score: ${c.risk_score}</span></td>
                <td><span class="badge ${statusClass}">${c.status}</span></td>
                <td style="font-size:13px; color:var(--text-secondary);">
                    ${c.last_action_taken ? `<code>${c.last_action_taken}</code>` : '<span style="color:var(--text-muted);">Awaiting Analysis</span>'}
                </td>
                <td style="text-align:center;">${c.recovery_attempts}/${c.max_allowed_attempts}</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        ${c.status === 'DETECTED' ? `
                            <button class="btn btn-primary btn-sm" onclick="analyzeCase('${c.id}')" title="Run Gemini AI Diagnosis">
                                ⚡ Analyze
                            </button>
                        ` : ''}
                        ${c.status === 'ACTION_REQUIRED' ? `
                            <button class="btn btn-gradient btn-sm" onclick="executeAction('${c.id}')" title="Execute Bounded Action">
                                🚀 Execute
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary btn-sm btn-icon" onclick="openAuditModal('${c.id}')" title="View Explainability Audit Trail">
                            📜 Audit
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Case Action Handlers
async function analyzeCase(caseId) {
    showToast('Running Gemini AI Root Cause Analysis...', 'info');
    try {
        const res = await fetch(`${API_BASE}/cases/${caseId}/analyze`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            showToast(`AI Recommended: ${data.reasoning.recommended_action} (${(data.reasoning.confidence_score * 100).toFixed(0)}% confidence)`, 'success');
            await refreshDashboard();
        } else {
            showToast('AI Analysis failed', 'error');
        }
    } catch (err) {
        showToast('Error invoking AI agent', 'error');
    }
}

async function executeAction(caseId) {
    showToast('Executing safe bounded action via Razorpay...', 'info');
    try {
        const res = await fetch(`${API_BASE}/cases/${caseId}/execute`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            if (data.details && data.details.short_url) {
                showToast(`Payment Link Generated: ${data.details.short_url}`, 'success');
            } else {
                showToast(`Executed: ${data.executed_action}`, 'success');
            }
            await refreshDashboard();
        } else {
            const err = await res.json();
            showToast(err.detail || 'Execution blocked by guardrail', 'error');
        }
    } catch (err) {
        showToast('Error executing action', 'error');
    }
}

// Open Audit Modal
async function openAuditModal(caseId) {
    const modal = document.getElementById('modalAudit');
    const container = document.getElementById('auditTimelineContainer');
    document.getElementById('auditCaseSubtitle').innerText = `Case ID: ${caseId}`;
    container.innerHTML = '<div style="color:var(--text-muted);">Fetching immutable audit trail...</div>';
    modal.classList.add('open');

    try {
        const res = await fetch(`${API_BASE}/cases/${caseId}/audit-logs`, { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            const logs = data.audit_logs || [];

            if (logs.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); padding:20px 0;">No audit records logged yet for this case. Run "Analyze" to generate AI telemetry.</div>';
                return;
            }

            container.innerHTML = logs.map(log => {
                const isSuccess = log.execution_status === 'SUCCESS';
                const isBlocked = log.execution_status === 'BLOCKED_BY_GUARDRAIL';
                const dotClass = isBlocked ? 'danger' : isSuccess ? 'success' : '';

                return `
                    <div class="timeline-item">
                        <div class="timeline-dot ${dotClass}"></div>
                        <div class="timeline-content">
                            <div class="timeline-header">
                                <span class="timeline-type">${log.event_type}</span>
                                <span class="timeline-time">${new Date(log.created_at).toLocaleString()}</span>
                            </div>
                            <div class="timeline-reasoning">${log.ai_reasoning || 'No explanation recorded'}</div>
                            <div class="timeline-meta">
                                <strong>Recommended:</strong> <code>${log.recommended_action}</code> | 
                                <strong>Status:</strong> <span class="badge ${isBlocked ? 'badge-failed' : 'badge-recovered'}">${log.execution_status}</span>
                                ${log.confidence_score ? ` | <strong>Confidence:</strong> ${(log.confidence_score * 100).toFixed(0)}%` : ''}
                            </div>
                            ${log.prompt_context ? `
                                <details style="margin-top:10px; font-size:12px; color:var(--text-muted); cursor:pointer;">
                                    <summary>View Prompt & Policy Context</summary>
                                    <pre style="background:rgba(0,0,0,0.4); padding:10px; border-radius:6px; margin-top:6px; overflow-x:auto;">${JSON.stringify(log.prompt_context, null, 2)}</pre>
                                </details>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (err) {
        container.innerHTML = '<div style="color:var(--danger);">Failed to load audit logs.</div>';
    }
}

// Load Policies Modal
async function loadPolicies() {
    const container = document.getElementById('policiesListContainer');
    container.innerHTML = '<div style="color:var(--text-muted);">Loading active policies...</div>';

    try {
        const res = await fetch(`${API_BASE}/policies`, { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            const policies = data.policies || [];

            if (policies.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted);">No custom policies configured. Standard retry policy is active.</div>';
                return;
            }

            container.innerHTML = policies.map(p => `
                <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:8px; padding:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <strong>${p.title}</strong>
                        <span class="badge badge-action">${p.policy_type}</span>
                    </div>
                    <div style="font-size:13px; color:var(--text-secondary);">${p.content}</div>
                </div>
            `).join('');
        }
    } catch (err) {
        container.innerHTML = '<div style="color:var(--danger);">Error loading policies.</div>';
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}
