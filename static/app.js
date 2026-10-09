document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    // UI Sections
    const uploadSection = document.getElementById('upload-section');
    const pipelineSection = document.getElementById('pipeline-section');
    const confirmSection = document.getElementById('confirm-section');
    const resultsSection = document.getElementById('results-section');
    const btnConfirmMeds = document.getElementById('btn-confirm-meds');
    
    // Global state for processed data
    let processedData = null;
    let currentLang = 'en';

    // Drag and Drop Logic
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        uploadSection.classList.add('hidden-view');
        pipelineSection.classList.remove('hidden-view');
        
        // Start extractor animation
        const extractorStep = document.getElementById('step-extractor');
        extractorStep.classList.remove('pending');
        extractorStep.classList.add('active');

        // Upload to real backend
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Extraction failed");
            }
            
            const data = await response.json();
            processedData = { extractor: data.extractor };
            
            // Auto-detect language
            if (processedData.extractor.patient_language === 'es') {
                currentLang = 'es';
                langButtons.forEach(b => b.classList.remove('active'));
                document.querySelector('.btn-lang[data-lang="es"]').classList.add('active');
            }
            
            extractorStep.classList.remove('active');
            extractorStep.classList.add('complete');

            // Show Confirm Meds Step
            setTimeout(() => {
                pipelineSection.classList.add('hidden-view');
                confirmSection.classList.remove('hidden-view');
                renderConfirmStep();
            }, 500);

        } catch (error) {
            console.error('Error extracting data:', error);
            alert(`Failed to extract document: ${error.message}\nMake sure your FEATHERLESS_API_KEY is set in .env!`);
            resetApp();
        }
    }

    function renderConfirmStep() {
        const medsListContainer = document.getElementById('meds-list-container');
        medsListContainer.innerHTML = '';
        
        processedData.extractor.medications.forEach(med => {
            const item = document.createElement('div');
            item.className = 'med-confirm-item';
            item.innerHTML = `
                <div class="med-info">
                    <strong>${med.name}</strong> ${med.dose}
                    <div class="med-freq">${med.frequency}</div>
                </div>
                <div class="med-source">
                    <span class="icon">🔍</span> Extracted from <a href="#" class="source-link">${med.source}</a>
                </div>
            `;
            medsListContainer.appendChild(item);
        });
    }

    if (btnConfirmMeds) {
        btnConfirmMeds.addEventListener('click', async () => {
            confirmSection.classList.add('hidden-view');
            pipelineSection.classList.remove('hidden-view');
            
            const steps = ['safety', 'explainer', 'scheduler'];
            steps.forEach(s => {
                const el = document.getElementById(`step-${s}`);
                el.classList.remove('pending');
                el.classList.add('active');
            });

            try {
                // Call real agents
                const response = await fetch('/api/generate_plan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(processedData.extractor)
                });
                
                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Plan generation failed");
                }
                
                const planData = await response.json();
                
                // Merge data
                processedData.safety_check = planData.safety_check;
                processedData.explainer = planData.explainer;
                processedData.scheduler = planData.scheduler;

                steps.forEach(s => {
                    const el = document.getElementById(`step-${s}`);
                    el.classList.remove('active');
                    el.classList.add('complete');
                });

                renderDashboard();
                
                setTimeout(() => {
                    pipelineSection.classList.add('hidden-view');
                    resultsSection.classList.remove('hidden-view');
                }, 800);

            } catch (error) {
                console.error('Error generating plan:', error);
                alert(`Failed to generate plan: ${error.message}`);
                resetApp();
            }
        });
    }

    function renderDashboard() {
        if (!processedData) return;

        // Explainer Content
        const summaryEl = document.getElementById('summary-content');
        if (summaryEl) {
            summaryEl.innerHTML = '';
            const summaryData = processedData.explainer[`summary_${currentLang}`];
            if (summaryData) {
                summaryData.forEach(point => {
                    const li = document.createElement('li');
                    li.textContent = point;
                    summaryEl.appendChild(li);
                });
            }
        }
        
        // Diet and Activity Content
        const dietEl = document.getElementById('diet-content');
        if (dietEl) {
            dietEl.innerHTML = '';
            const dietData = processedData.explainer[`diet_activity_${currentLang}`];
            if (dietData && dietData.length > 0 && dietData[0].toLowerCase() !== 'none') {
                document.querySelector('.diet-card').style.display = 'flex';
                dietData.forEach(point => {
                    const li = document.createElement('li');
                    li.textContent = point;
                    dietEl.appendChild(li);
                });
            } else {
                document.querySelector('.diet-card').style.display = 'none';
            }
        }

        // Safety Content
        const safetyContainer = document.getElementById('safety-details-container');
        if (safetyContainer) {
            safetyContainer.innerHTML = '';
            const flags = processedData.safety_check.flags;
            if (processedData.safety_check.error) {
                safetyContainer.innerHTML = `<div class="status-badge danger">Error</div><p style="color:var(--text-primary); font-weight:bold;">${processedData.safety_check.error}</p>`;
            } else if (flags && flags.length > 0) {
                flags.forEach(flag => {
                    const isHigh = flag.severity === 'high';
                    const headline = flag[`headline_${currentLang}`];
                    const action = flag[`action_${currentLang}`];
                    const detail = flag[`detail_${currentLang}`];
                    
                    const flagEl = document.createElement('div');
                    flagEl.className = `safety-flag ${flag.severity}`;
                    flagEl.innerHTML = `
                        <div class="status-badge ${isHigh ? 'danger' : 'warning'}">${isHigh ? 'High Risk' : 'Warning'}</div>
                        <h4>${headline}</h4>
                        <div class="safety-action"><strong>${action}</strong></div>
                        <p>${detail}</p>
                        <div class="safety-citation" style="font-size:0.8em; color:var(--text-secondary); margin-top:5px;"><em>${flag.citation}</em></div>
                    `;
                    safetyContainer.appendChild(flagEl);
                });
            } else {
                const safeText = currentLang === 'es' ? 'Sin conflictos' : 'No Conflicts';
                const safeDesc = currentLang === 'es' ? 'No se encontraron interacciones mayores.' : 'No major interactions found.';
                safetyContainer.innerHTML = `<div class="status-badge safe">${safeText}</div><p>${safeDesc}</p>`;
            }
        }

        // Timeline
        const timelineContainer = document.getElementById('timeline-container');
        if (timelineContainer) {
            timelineContainer.innerHTML = '';
            const timelineData = processedData.scheduler[`timeline_${currentLang}`];
            if (timelineData) {
                timelineData.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'timeline-item';
                    
                    // Inject warning dynamically from safety flags
                    let actionHtml = item.action;
                    let warningsHtml = '';
                    
                    if (processedData.safety_check && processedData.safety_check.flags) {
                        processedData.safety_check.flags.forEach(flag => {
                            flag.drugs.forEach(drug => {
                                // Simple string match. If the drug name is in the action string
                                // Note: drug string from LLM might be "NSAID (Ibuprofen)", so we split or lowercase check.
                                const cleanDrug = drug.replace(/.*\((.*?)\).*/, '$1').trim().toLowerCase();
                                if (actionHtml.toLowerCase().includes(cleanDrug)) {
                                    warningsHtml += `<div class="inline-warning">⚠ ${flag[`action_${currentLang}`]}</div>`;
                                }
                            });
                        });
                    }
                    
                    div.innerHTML = `
                        <div class="timeline-time">${item.time}</div>
                        <div class="timeline-action">${actionHtml}${warningsHtml}</div>
                    `;
                    timelineContainer.appendChild(div);
                });
            }
        }

        // Warnings
        const docWarningList = document.getElementById('doc-warning-list');
        const genWarningList = document.getElementById('gen-warning-list');
        
        if (docWarningList && processedData.scheduler[`doc_warnings_${currentLang}`]) {
            docWarningList.innerHTML = '';
            processedData.scheduler[`doc_warnings_${currentLang}`].forEach(warning => {
                const li = document.createElement('li');
                li.textContent = warning;
                docWarningList.appendChild(li);
            });
        }
        
        if (genWarningList && processedData.scheduler[`general_warnings_${currentLang}`]) {
            genWarningList.innerHTML = '';
            processedData.scheduler[`general_warnings_${currentLang}`].forEach(warning => {
                const li = document.createElement('li');
                li.textContent = warning;
                genWarningList.appendChild(li);
            });
        }
    }

    // Language Toggle
    const langButtons = document.querySelectorAll('.btn-lang');
    langButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            langButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentLang = e.target.dataset.lang;
            renderDashboard();
        });
    });

    window.resetApp = function() {
        resultsSection.classList.add('hidden-view');
        confirmSection.classList.add('hidden-view');
        uploadSection.classList.remove('hidden-view');
        
        const steps = ['extractor', 'safety', 'explainer', 'scheduler'];
        steps.forEach((step, index) => {
            const el = document.getElementById(`step-${step}`);
            el.className = 'agent-step';
            if (index > 0) el.classList.add('pending');
        });
        
        fileInput.value = '';
    }
});
