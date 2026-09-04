// RecoverAI Production Frontend Application Controller

const API_BASE = '/api/v1';
let authToken = localStorage.getItem('recoverai_auth_token') || null;
let currentMerchant = null;
let currentFilter = 'ALL';
let allCases = [];

// App Lifecycle Initialization
document.addEventListener('DOMContentLoaded', async () => {
    setupAuthHandlers();
    setupDashboardHandlers();

    if (authToken) {
        await initAuthenticatedSession();
    } else {
        showAuthScreen();
    }
});

// View State Management
function showAuthScreen() {
    document.getElementById('authContainer').style.display = 'flex';
    document.getElementById('appContainer').style.display = 'none';
}

function showDashboardScreen() {
    document.getElementById('authContainer').style.display = 'none';
    document.getElementById('appContainer').style.display = 'block';
}

// Authentication Setup
function setupAuthHandlers() {
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');
    const formLogin = document.getElementById('formLogin');
    const formRegister = document.getElementById('formRegister');
    const linkGoRegister = document.getElementById('linkGoRegister');
    const linkGoLogin = document.getElementById('linkGoLogin');

    tabLogin.onclick = () => {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.style.display = 'block';
        formRegister.style.display = 'none';
        const cardTitle = document.getElementById('authCardTitle');
        if (cardTitle) cardTitle.innerText = 'Sign In';
    };

    tabRegister.onclick = () => {
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
        formRegister.style.display = 'block';
        formLogin.style.display = 'none';
        const cardTitle = document.getElementById('authCardTitle');
        if (cardTitle) cardTitle.innerText = 'Create Account';
    };

    if (linkGoRegister) linkGoRegister.onclick = () => tabRegister.click();
    if (linkGoLogin) linkGoLogin.onclick = () => tabLogin.click();

    // Check URL query, hash, or path for direct /register navigation
    const path = window.location.pathname.toLowerCase();
    const hash = window.location.hash.toLowerCase();
    if (path.includes('register') || hash.includes('register')) {
        tabRegister.click();
        setTimeout(() => document.getElementById('regName')?.focus(), 150);
    } else if (path.includes('login') || hash.includes('login')) {
        tabLogin.click();
        setTimeout(() => document.getElementById('loginEmail')?.focus(), 150);
    }

    // Handle Login
    formLogin.onsubmit = async (e) => {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (res.ok) {
                const data = await res.json();
                authToken = data.access_token;
                localStorage.setItem('recoverai_auth_token', authToken);
                showToast('Welcome back! Signed in successfully.', 'success');
                await initAuthenticatedSession();
            } else {
                const err = await res.json();
                showToast(err.detail || 'Invalid email or password.', 'error');
            }
        } catch (err) {
            showToast('Unable to reach server. Check connection.', 'error');
        }
    };

    // Handle Registration
    formRegister.onsubmit = async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('regName').value.trim(),
            email: document.getElementById('regEmail').value.trim(),
            password: document.getElementById('regPassword').value,
            razorpay_key_id: document.getElementById('regKeyId').value.trim() || null,
            razorpay_key_secret: document.getElementById('regKeySecret').value.trim() || null
        };

        try {
            const regRes = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (regRes.ok) {
                showToast('Account registered successfully! Signing in...', 'success');
                // Automatically log in
                const loginRes = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: payload.email, password: payload.password })
                });

                if (loginRes.ok) {
                    const data = await loginRes.json();
                    authToken = data.access_token;
                    localStorage.setItem('recoverai_auth_token', authToken);
                    await initAuthenticatedSession();
                }
            } else {
                const err = await regRes.json();
                showToast(err.detail || 'Registration failed.', 'error');
            }
        } catch (err) {
            showToast('Unable to register account. Check server connection.', 'error');
        }
    };
}

// Session Initialization
async function initAuthenticatedSession() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
        if (res.ok) {
            currentMerchant = await res.json();
            document.getElementById('merchantNameDisplay').innerText = currentMerchant.name;
            document.getElementById('merchantAvatar').innerText = currentMerchant.name.charAt(0).toUpperCase();

            // Set live webhook URL in configuration modal
            const webhookUrl = `${window.location.origin}${API_BASE}/webhooks/razorpay`;
            document.getElementById('webhookUrlDisplay').value = webhookUrl;

            showDashboardScreen();
            await refreshDashboard();
        } else {
            // Token expired or invalid
            logoutMerchant();
        }
    } catch (err) {
        logoutMerchant();
    }
}

function logoutMerchant() {
    authToken = null;
    currentMerchant = null;
    localStorage.removeItem('recoverai_auth_token');
    showAuthScreen();
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}

// Dashboard Event Handlers
function setupDashboardHandlers() {
    // Logout
    document.getElementById('btnLogout').onclick = () => {
        logoutMerchant();
        showToast('You have been signed out.', 'info');
    };

    // Switch / Register New Merchant
    const btnSwitchMerchant = document.getElementById('btnSwitchMerchant');
    if (btnSwitchMerchant) {
        btnSwitchMerchant.onclick = () => {
            logoutMerchant();
            const tabRegister = document.getElementById('tabRegister');
            if (tabRegister) tabRegister.click();
            showToast('Ready to register or switch merchant workspace.', 'info');
            setTimeout(() => document.getElementById('regName')?.focus(), 150);
        };
    }

    // Modals
    const modalSimulate = document.getElementById('modalSimulate');
    const modalAudit = document.getElementById('modalAudit');
    const modalPolicies = document.getElementById('modalPolicies');
    const modalWebhookConfig = document.getElementById('modalWebhookConfig');

    document.getElementById('btnSimulateModal').onclick = () => modalSimulate.classList.add('open');
    document.getElementById('btnCloseSimulate').onclick = () => modalSimulate.classList.remove('open');
    document.getElementById('btnCancelSimulate').onclick = () => modalSimulate.classList.remove('open');

    document.getElementById('btnCloseAudit').onclick = () => modalAudit.classList.remove('open');

    document.getElementById('btnOpenPolicies').onclick = () => {
        loadPolicies();
        modalPolicies.classList.add('open');
    };
    document.getElementById('btnClosePolicies').onclick = () => modalPolicies.classList.remove('open');

    document.getElementById('btnOpenWebhookConfig').onclick = () => modalWebhookConfig.classList.add('open');
    document.getElementById('btnCloseWebhookConfig').onclick = () => modalWebhookConfig.classList.remove('open');

    // Copy Webhook URL
    document.getElementById('btnCopyWebhook').onclick = () => {
        const input = document.getElementById('webhookUrlDisplay');
        input.select();
        navigator.clipboard.writeText(input.value);
        showToast('Webhook URL copied to clipboard!', 'success');
    };

    // Simulate Event Submission
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
                showToast('⚡ Failure event processed! Risk categorized and recovery case created.', 'success');
                modalSimulate.classList.remove('open');
                await refreshDashboard();
            } else {
                showToast('Failed to ingest event', 'error');
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
            showToast('No pending cases currently require recovery.', 'info');
            return;
        }

        showToast(`Running autonomous recovery across ${actionableCases.length} cases...`, 'info');

        for (const c of actionableCases) {
            if (c.status === 'DETECTED') {
                await fetch(`${API_BASE}/cases/${c.id}/analyze`, { method: 'POST', headers: getAuthHeaders() });
            }
            await fetch(`${API_BASE}/cases/${c.id}/execute`, { method: 'POST', headers: getAuthHeaders() });
        }

        showToast('Autonomous recovery pipeline completed!', 'success');
        await refreshDashboard();
    };

    // Quick Policy Templates
    const btnTplHighValue = document.getElementById('btnTplHighValue');
    const btnTplTimeout = document.getElementById('btnTplTimeout');
    const btnTplGuardrail = document.getElementById('btnTplGuardrail');

    if (btnTplHighValue) {
        btnTplHighValue.onclick = () => {
            document.getElementById('policyTitle').value = 'VIP High-Value Order Recovery SLA';
            document.getElementById('policyType').value = 'RETRY';
            document.getElementById('policyContent').value = 'For failed orders above ₹5,000 caused by bank timeouts or network latency, do not wait; generate a secure Razorpay Payment Link with 24-hour validity and send an immediate recovery notification to the customer. Limit retries to 3 attempts.';
            showToast('High-Value SLA template loaded into form.', 'info');
        };
    }

    if (btnTplTimeout) {
        btnTplTimeout.onclick = () => {
            document.getElementById('policyTitle').value = 'Bank Network Timeout Protocol';
            document.getElementById('policyType').value = 'RETRY';
            document.getElementById('policyContent').value = 'When a transaction fails with BAD_REQUEST_PAYMENT_TIMED_OUT or GATEWAY_ERROR, automatically generate a Razorpay Payment Link and dispatch to the customer verified email. Do not cancel the order.';
            showToast('Bank Timeout Protocol template loaded.', 'info');
        };
    }

    if (btnTplGuardrail) {
        btnTplGuardrail.onclick = () => {
            document.getElementById('policyTitle').value = 'Strict Zero-Refund & Value-Lock Guardrail';
            document.getElementById('policyType').value = 'REFUND';
            document.getElementById('policyContent').value = 'Under no circumstances should the recovery agent initiate a refund or alter the transaction value. All unrecoverable cases must be escalated to operations review.';
            showToast('Zero-Refund Guardrail template loaded.', 'info');
        };
    }

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
            showToast('Policy rule vector-indexed for Gemini RAG retrieval!', 'success');
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
        tbody.innerHTML = `<tr><td colspan="8" class="table-empty">No recovery cases found for "${currentFilter}". Use "+ Ingest Event" or send Razorpay webhooks.</td></tr>`;
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
    showToast('Running Gemini AI Root Cause Analysis with RAG Policies...', 'info');
    try {
        const res = await fetch(`${API_BASE}/cases/${caseId}/analyze`, {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (res.ok) {
            const data = await res.json();
            showToast(`AI Diagnosis: ${data.reasoning.recommended_action} (${(data.reasoning.confidence_score * 100).toFixed(0)}% confidence)`, 'success');
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
                container.innerHTML = '<div style="color:var(--text-muted); padding:20px 0;">No audit records logged yet. Run "Analyze" to generate AI telemetry.</div>';
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
    container.innerHTML = '<div style="color:var(--text-muted);">Loading active merchant policies...</div>';

    try {
        const res = await fetch(`${API_BASE}/policies`, { headers: getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            const policies = data.policies || [];

            if (policies.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted);">No custom policies configured. Standard merchant retry policy is active.</div>';
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
