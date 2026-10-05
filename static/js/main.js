/* RouteWise - main.js */

// Utility: format BDT with commas (en-IN)
function formatBDT(num){
  if (num === null || num === undefined || num === "") return "0";
  const n = Number(String(num).replace(/,/g, ""));
  if (isNaN(n)) return String(num);
  return n.toLocaleString('en-IN');
}
function parseBDT(val){
  if (val === null || val === undefined) return 0;
  return Number(String(val).replace(/,/g, "").replace(/ /g, "")) || 0;
}

// 1. Incident card selection (incident.html)
(function initIncidentSelection(){
  const cards = document.querySelectorAll('.incident-card');
  const input = document.getElementById('incident_type_input');
  const btn = document.getElementById('analyzeBtn');
  if (!cards.length || !input) return;
  cards.forEach(card=>{
    card.addEventListener('click', ()=>{
      cards.forEach(c=>c.classList.remove('selected'));
      card.classList.add('selected');
      const val = card.getAttribute('data-incident');
      input.value = val;
      cards.forEach(c=>{
        const chk = c.querySelector('.incident-check');
        if(chk) chk.textContent = '○';
      });
      const chk = card.querySelector('.incident-check');
      if(chk) chk.textContent = '●';
      if(btn) btn.disabled = false;
    });
    card.addEventListener('keydown', (e)=>{
      if(e.key==='Enter' || e.key===' '){
        e.preventDefault();
        card.click();
      }
    });
  });
})();

// 4. Form validation & BDT formatting (shipment.html) with Recovery Budget vs Total Payment warning
(function initShipmentValidation(){
  const form = document.getElementById('shipmentForm');
  if(!form) return;
  const origin = document.getElementById('origin');
  const dest = document.getElementById('destination');
  const err = document.getElementById('destError');
  
  const bdtFields = ['cargo_value_bdt','original_cost_bdt','total_payment_received_bdt','recovery_budget_bdt'];
  const weightField = document.getElementById('cargo_weight_tons');
  const budgetField = document.getElementById('recovery_budget_bdt');
  const paymentField = document.getElementById('total_payment_received_bdt');
  const budgetWarning = document.getElementById('budgetWarning');
  const budgetHint = document.getElementById('budgetHint');
  const paymentHint = document.getElementById('paymentHint');
  const cargoValueField = document.getElementById('cargo_value_bdt');
  
  function stripCommas(val){
    return String(val).replace(/,/g, '').trim();
  }

  // Auto-suggest Total Payment as cargo_value *1.25
  function updatePaymentHint(){
    if(!cargoValueField || !paymentField) return;
    const cargoVal = parseBDT(cargoValueField.value);
    const paymentVal = parseBDT(paymentField.value);
    if(cargoVal && !paymentVal){
      const suggested = Math.round(cargoVal * 1.25);
      if(paymentHint){
        paymentHint.textContent = `Suggested: BDT ${formatBDT(suggested)} (cargo ×1.25). Leave as is or edit.`;
        paymentHint.style.display = 'block';
      }
    } else if(paymentHint){
      paymentHint.style.display = 'none';
    }
  }
  if(cargoValueField){
    cargoValueField.addEventListener('blur', updatePaymentHint);
    cargoValueField.addEventListener('input', updatePaymentHint);
  }

  function checkBudgetVsPayment(){
    if(!budgetField || !paymentField) return true;
    const budget = parseBDT(budgetField.value);
    const payment = parseBDT(paymentField.value);
    if(!budget || !payment){
      if(budgetWarning) budgetWarning.style.display='none';
      if(budgetHint) budgetHint.style.display='none';
      budgetField.style.borderColor='';
      return true;
    }
    if(budget > payment){
      if(budgetWarning){
        budgetWarning.textContent = `⚠ Recovery Budget (BDT ${formatBDT(budget)}) exceeds Total Payment Received (BDT ${formatBDT(payment)}) — recovery cost cannot exceed payment! Increase payment or lower budget.`;
        budgetWarning.style.display='block';
      }
      budgetField.style.borderColor='#f59e0b';
      if(budgetHint){
        const diff = budget - payment;
        budgetHint.textContent = `Need at least BDT ${formatBDT(diff)} reduction or increase payment to cover. With 1000 routes, cheapest recovery ≈ BDT 8k-15k, but budget ${formatBDT(budget)} > payment will cause loss.`;
        budgetHint.style.display='block';
      }
      // Warning only, don't block typing, but will show in output recommendation
      return true;
    } else {
      if(budgetWarning) budgetWarning.style.display='none';
      budgetField.style.borderColor='';
      if(budgetHint){
        const remaining = payment - budget;
        budgetHint.textContent = `✓ Within payment — BDT ${formatBDT(remaining)} remaining after recovery.`;
        budgetHint.style.display='block';
      }
      return true;
    }
  }

  // Attach live warning
  if(budgetField) {
    budgetField.addEventListener('input', checkBudgetVsPayment);
    budgetField.addEventListener('blur', ()=>{
      if(budgetField.value){
        const raw = stripCommas(budgetField.value);
        if(raw && !isNaN(raw)){
          budgetField.value = Number(raw).toLocaleString('en-IN');
        }
      }
      checkBudgetVsPayment();
    });
  }
  if(paymentField){
    paymentField.addEventListener('input', checkBudgetVsPayment);
    paymentField.addEventListener('blur', ()=>{
      if(paymentField.value){
        const raw = stripCommas(paymentField.value);
        if(raw && !isNaN(raw)){
          paymentField.value = Number(raw).toLocaleString('en-IN');
        }
      }
      checkBudgetVsPayment();
    });
  }

  // Generic BDT formatting for other fields
  bdtFields.forEach(id=>{
    const el = document.getElementById(id);
    if(!el || el===budgetField || el===paymentField) return; // already handled
    el.addEventListener('blur', ()=>{
      if(el.value){
        const raw = stripCommas(el.value);
        if(raw && !isNaN(raw)){
          el.value = Number(raw).toLocaleString('en-IN');
        }
      }
      el.setCustomValidity('');
      if(id==='cargo_value_bdt') updatePaymentHint();
    });
    el.addEventListener('focus', ()=>{
      if(el.value){
        el.value = stripCommas(el.value);
        setTimeout(()=>el.select(), 10);
      }
    });
    el.addEventListener('input', ()=>{
      let v = el.value.replace(/[^0-9,]/g, '');
      if(v !== el.value) el.value = v;
      el.setCustomValidity('');
    });
  });
  
  // Handle focus for budget/payment separately to avoid double handling
  [budgetField, paymentField].forEach(el=>{
    if(!el) return;
    el.addEventListener('focus', ()=>{
      if(el.value){
        el.value = stripCommas(el.value);
        setTimeout(()=>el.select(), 10);
      }
    });
    el.addEventListener('input', ()=>{
      let v = el.value.replace(/[^0-9,]/g, '');
      if(v !== el.value) el.value = v;
      el.setCustomValidity('');
    });
  });
  
  if(weightField){
    weightField.addEventListener('input', ()=> weightField.setCustomValidity(''));
  }

  function validateOriginDest(){
    if(!origin || !dest) return true;
    if(origin.value && dest.value && origin.value===dest.value){
      if(err) {err.style.display='block'; err.textContent='Origin and destination must be different';}
      dest.style.borderColor='#ef4444';
      dest.setCustomValidity('Origin and destination must be different');
      return false;
    } else {
      if(err) err.style.display='none';
      dest.style.borderColor='';
      dest.setCustomValidity('');
      return true;
    }
  }
  if(origin) origin.addEventListener('change', validateOriginDest);
  if(dest) dest.addEventListener('change', validateOriginDest);

  form.addEventListener('submit', (e)=>{
    bdtFields.forEach(id=>{
      const el=document.getElementById(id);
      if(el && el.value){
        el.value = stripCommas(el.value);
      }
    });
    if(weightField && weightField.value){
      weightField.value = String(weightField.value).replace(/,/g, '');
    }

    let valid = true;
    const required = form.querySelectorAll('[required]');
    required.forEach(el=>{
      if(!el.value || !el.value.trim()){
        el.style.borderColor='#ef4444';
        valid=false;
      } else {
        el.style.borderColor='';
        el.setCustomValidity('');
        const val = parseBDT(el.value);
        if(el.id==='cargo_weight_tons'){
          if(isNaN(val) || val < 1 || val > 200){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Weight must be between 1 and 200 tons');
            valid=false;
          }
        } else if(el.id==='cargo_value_bdt'){
          if(isNaN(val) || val < 1000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Cargo value must be at least 1,000 BDT');
            valid=false;
          } else if(val > 100000000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Cargo value too large for simulation (max 100M)');
            valid=false;
          }
        } else if(el.id==='original_cost_bdt'){
          if(isNaN(val) || val < 1000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Original cost must be at least 1,000 BDT');
            valid=false;
          }
        } else if(el.id==='total_payment_received_bdt'){
          if(isNaN(val) || val < 1000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Total Payment must be at least 1,000 BDT');
            valid=false;
          }
        } else if(el.id==='recovery_budget_bdt'){
          if(isNaN(val) || val < 5000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Recovery budget must be at least 5,000 BDT');
            valid=false;
          } else if(val > 10000000){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Budget too high (max 10M for simulation)');
            valid=false;
          }
        } else if(el.id==='delivery_deadline_days'){
          if(isNaN(val) || val < 1 || val > 60){
            el.style.borderColor='#ef4444';
            el.setCustomValidity('Deadline must be 1-60 days');
            valid=false;
          }
        }
      }
    });
    // Check budget vs payment - warning, not blocking, but if budget > payment we still allow submit but user has been warned
    // We don't set valid=false for this, just warning already shown
    if(!validateOriginDest()) valid=false;
    
    if(!valid){
      e.preventDefault();
      const firstInvalid = form.querySelector(':invalid');
      if(firstInvalid){
        firstInvalid.reportValidity();
        firstInvalid.scrollIntoView({behavior:'smooth', block:'center'});
      } else {
        const firstErr = form.querySelector('[style*="border-color: rgb(239, 68, 68)"]');
        if(firstErr) firstErr.scrollIntoView({behavior:'smooth', block:'center'});
      }
      bdtFields.forEach(id=>{
        const el=document.getElementById(id);
        if(el && el.value && !isNaN(el.value)){
          el.value = Number(el.value).toLocaleString('en-IN');
        }
      });
    }
  });
  
  window.addEventListener('load', ()=>{
    bdtFields.forEach(id=>{
      const el=document.getElementById(id);
      if(el && el.value){
        const raw = stripCommas(el.value);
        if(raw && !isNaN(raw) && raw.indexOf(',')===-1){
          try{ el.value = Number(raw).toLocaleString('en-IN'); }catch{}
        }
      }
    });
    updatePaymentHint();
    checkBudgetVsPayment();
  });
  // Initial check after a short delay
  setTimeout(()=>{ updatePaymentHint(); checkBudgetVsPayment(); }, 500);
})();

// 2. Processing page runner
async function runProcessingPipeline(){
  const steps = ['step1','step2','step3','step4','step5','step6','step7'];
  const detailsIds = ['step1-detail','step2-detail','step3-detail','step4-detail','step5-detail','step6-detail','step7-detail'];
  const statusIds = ['step1-status','step2-status','step3-status','step4-status','step5-status','step6-status','step7-status'];
  function showStep(idx, detailText, isComplete){
    const el = document.getElementById(steps[idx]);
    const detail = document.getElementById(detailsIds[idx]);
    const status = document.getElementById(statusIds[idx]);
    if(el){
      el.classList.add('visible');
      if(isComplete) el.classList.add('complete');
      else el.classList.add('active');
    }
    if(detail && detailText) detail.textContent = detailText;
    if(status){
      const dot = status.querySelector('.status-dot');
      if(dot && isComplete) dot.style.background='#10b981';
    }
  }
  function markComplete(idx){
    const el = document.getElementById(steps[idx]);
    if(el){
      el.classList.remove('active');
      el.classList.add('complete');
    }
  }
  showStep(0, null, false);
  try {
    const response = await fetch('/run_analysis', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({})
    });
    const data = await response.json();
    if(data.status !== 'complete'){
      // If budget exceeds payment but has recommendation, still show
      if(data.results && data.results.financial){
        // continue to show steps even with warning
      } else {
        throw new Error(data.message || 'Analysis failed');
      }
    }
    const r = data.results;
    await delay(600);
    markComplete(0);
    showStep(1, null, false);
    await delay(800);
    const csp = r.csp_metrics || r.csp || {};
    const cspDetail = `${csp.total_checked ?? csp.options_checked ?? 0} options checked, ${csp.removed ?? csp.options_removed ?? 0} removed, ${csp.passed ?? csp.options_passed ?? 0} remain`;
    const s2 = document.getElementById('step2-detail');
    if(s2) s2.textContent = cspDetail + ` — ${csp.execution_time_ms ?? 0} ms`;
    markComplete(1);
    showStep(2, null, false);
    await delay(800);
    const dijk = r.dijkstra_route || {};
    const dijkCost = dijk.cost ?? dijk.total_cost ?? 0;
    const dijkTimeHrs = dijk.time ?? dijk.total_time ?? 0;
    const dijkTimeDays = (dijkTimeHrs/24).toFixed(2);
    const dijkDetail = `Route found: BDT ${formatBDT(dijkCost)}, ${dijkTimeHrs.toFixed(1)} hrs (${dijkTimeDays} days) via ${(dijk.path||[]).join(' → ')}`;
    const s3 = document.getElementById('step3-detail');
    if(s3) s3.textContent = dijkDetail;
    markComplete(2);
    showStep(3, null, false);
    await delay(800);
    const ast = r.astar_route || {};
    const astCost = ast.cost ?? ast.total_cost ?? 0;
    const astTimeHrs = ast.time ?? ast.total_time ?? 0;
    const astTimeDays = (astTimeHrs/24).toFixed(2);
    const astDetail = `Route found: BDT ${formatBDT(astCost)}, ${astTimeHrs.toFixed(1)} hrs (${astTimeDays} days) via ${(ast.path||[]).join(' → ')}`;
    const s4 = document.getElementById('step4-detail');
    if(s4) s4.textContent = astDetail;
    markComplete(3);
    showStep(4, null, false);
    await delay(800);
    const hill = r.hill_climbing_decision || r.hill_result || {};
    const diff = hill.cost_difference ?? 0;
    const perc = hill.percentage_difference ?? 0;
    const cls = hill.classification ?? hill.decision_type ?? '';
    const sel = hill.selected ?? '';
    const hillDetail = `Percentage diff ${perc}% (${cls}, threshold 5%), BDT ${formatBDT(diff)}, ${sel} selected — ${hill.reason ?? hill.rule_applied ?? ''}`;
    const s5 = document.getElementById('step5-detail');
    if(s5) s5.textContent = hillDetail;
    markComplete(4);
    showStep(5, null, false);
    await delay(700);
    const fin = r.financial || {};
    const finDetail = `Revenue BDT ${formatBDT(fin.revenue)} − Recovery BDT ${formatBDT(fin.recovery_cost)} = Profit BDT ${formatBDT(fin.final_profit)}${fin.budget_exceeds_payment ? ' ⚠ Budget exceeded payment!' : ''}`;
    const s6 = document.getElementById('step6-detail');
    if(s6) s6.textContent = finDetail;
    markComplete(5);
    showStep(6, null, false);
    await delay(700);
    const totalTime = r.evaluation?.total_execution_time_ms ?? r.total_execution_time_ms ?? 0;
    const s7 = document.getElementById('step7-detail');
    if(s7) s7.textContent = `All algorithms executed in ${totalTime} ms — analysis complete${r.warnings && r.warnings.length ? ' (with warnings)' : ''}`;
    markComplete(6);
    const btn = document.getElementById('viewResultsBtn');
    if(btn) {
      btn.style.display='inline-flex';
      btn.style.animation='fadeIn 0.5s ease';
    }
    const spinner = document.querySelector('.spinner');
    if(spinner) spinner.style.borderTopColor='#10b981';
  } catch(err){
    console.error('Pipeline error', err);
    const errEl = document.getElementById('processingError');
    if(errEl){
      errEl.textContent = 'Error: ' + err.message;
      errEl.style.display='block';
    }
    steps.forEach((id, idx)=>{
      const el=document.getElementById(id);
      if(el) {el.classList.add('visible'); el.style.opacity='1';}
    });
  }
}
function delay(ms){ return new Promise(res=>setTimeout(res, ms)); }

// 3. Chart rendering (result.html)
(function initCharts(){
  const chartDataEl = document.getElementById('chartData');
  if(!chartDataEl) return;
  let chartData;
  try{
    chartData = JSON.parse(chartDataEl.textContent);
  }catch(e){
    console.error('chart data parse error', e);
    return;
  }
  if(typeof Chart==='undefined'){
    console.warn('Chart.js not loaded');
    return;
  }
  Chart.defaults.color = '#9ca3af';
  Chart.defaults.borderColor = '#374151';
  Chart.defaults.font.family = 'Inter';
  const commonOptions = {
    responsive:true,
    maintainAspectRatio:false,
    plugins:{
      legend:{display:false},
      title:{display:false, color:'#f9fafb', font:{weight:'700'}}
    },
    scales:{
      x:{grid:{color:'rgba(55,65,81,0.5)'}, ticks:{color:'#9ca3af'}},
      y:{grid:{color:'rgba(55,65,81,0.5)'}, ticks:{color:'#9ca3af'}, beginAtZero:true}
    }
  };
  const ctxTime = document.getElementById('chartTime');
  if(ctxTime){
    new Chart(ctxTime, {
      type:'bar',
      data:{
        labels: chartData.algo_labels || ["CSP","Dijkstra","A*","Hill Climbing"],
        datasets:[{
          label:'Time (ms)',
          data: chartData.algo_times || [0,0,0,0],
          backgroundColor:['#f59e0b','#10b981','#6366f1','#ec4899'],
          borderRadius:8,
          borderSkipped:false
        }]
      },
      options:{
        ...commonOptions,
        plugins:{
          ...commonOptions.plugins,
          title:{display:true, text:'Algorithm Execution Time (ms)', color:'#f9fafb', font:{size:13, weight:'700'}},
          tooltip:{backgroundColor:'#111827', titleColor:'#f9fafb', bodyColor:'#9ca3af', borderColor:'#374151', borderWidth:1}
        }
      }
    });
  }
  const ctxNodes = document.getElementById('chartNodes');
  if(ctxNodes){
    new Chart(ctxNodes, {
      type:'bar',
      data:{
        labels:['Dijkstra','A*'],
        datasets:[{
          label:'Nodes Explored',
          data: chartData.nodes_explored || [0,0],
          backgroundColor:['#10b981','#6366f1'],
          borderRadius:8
        }]
      },
      options:{
        ...commonOptions,
        plugins:{
          ...commonOptions.plugins,
          title:{display:true, text:'Nodes Explored During Search', color:'#f9fafb', font:{size:13, weight:'700'}}
        }
      }
    });
  }
  const ctxCSP = document.getElementById('chartCSP');
  if(ctxCSP){
    new Chart(ctxCSP, {
      type:'doughnut',
      data:{
        labels:['Removed','Passed'],
        datasets:[{
          data: chartData.csp_filtered || [0,0],
          backgroundColor:['#ef4444','#10b981'],
          borderWidth:0,
          hoverOffset:6
        }]
      },
      options:{
        responsive:true,
        maintainAspectRatio:false,
        plugins:{
          legend:{position:'bottom', labels:{color:'#9ca3af', padding:16, usePointStyle:true}},
          title:{display:true, text:'CSP Constraint Filtering', color:'#f9fafb', font:{size:13, weight:'700'}},
          tooltip:{backgroundColor:'#111827', titleColor:'#f9fafb', bodyColor:'#9ca3af', borderColor:'#374151', borderWidth:1}
        },
        cutout:'62%'
      }
    });
  }
  const ctxQuality = document.getElementById('chartQuality');
  if(ctxQuality){
    const costs = chartData.cost_comparison || [0,0];
    const times = chartData.time_comparison || [0,0];
    new Chart(ctxQuality, {
      type:'bar',
      data:{
        labels:['Dijkstra','A*'],
        datasets:[
          {
            label:'Cost (BDT)',
            data: costs,
            backgroundColor:'#f59e0b',
            yAxisID:'y',
            borderRadius:6
          },
          {
            label:'Time (days)',
            data: times,
            backgroundColor:'#1f2937',
            borderColor:'#9ca3af',
            borderWidth:1,
            yAxisID:'y1',
            borderRadius:6
          }
        ]
      },
      options:{
        responsive:true,
        maintainAspectRatio:false,
        interaction:{mode:'index', intersect:false},
        plugins:{
          legend:{position:'bottom', labels:{color:'#9ca3af', usePointStyle:true}},
          title:{display:true, text:'Route Comparison: Cost and Time', color:'#f9fafb', font:{size:13, weight:'700'}},
          tooltip:{backgroundColor:'#111827', titleColor:'#f9fafb', bodyColor:'#9ca3af', borderColor:'#374151', borderWidth:1}
        },
        scales:{
          x:{grid:{color:'rgba(55,65,81,0.3)'}, ticks:{color:'#9ca3af'}},
          y:{
            type:'linear',
            position:'left',
            title:{display:true, text:'Cost (BDT)', color:'#f59e0b'},
            grid:{color:'rgba(55,65,81,0.3)'},
            ticks:{color:'#f59e0b'}
          },
          y1:{
            type:'linear',
            position:'right',
            title:{display:true, text:'Time (days)', color:'#9ca3af'},
            grid:{drawOnChartArea:false},
            ticks:{color:'#9ca3af'}
          }
        }
      }
    });
  }
})();

document.addEventListener('DOMContentLoaded', ()=>{
  document.querySelectorAll('.format-bdt').forEach(el=>{
    el.textContent = formatBDT(el.textContent);
  });
});
