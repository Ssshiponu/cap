function steps() {
    return {
        step: window.location.hash ? parseInt(window.location.hash.replace('#step-', '')) : 1,
        maxStep: 6,
        nextStep() {
            if (this.step < this.maxStep) {
                this.step++;
                window.location.hash = `#step-${this.step}`;
            }
        },
        backStep() {
            if (this.step > 1) {
                this.step--;
                window.location.hash = `#step-${this.step}`;
            }
        },
        nextStepText() {
            return (this.step === this.maxStep) ? 'Finish' : 'Next';
        }
    }
}


function main() {
    return {
        sidebar: window.innerWidth > 1023,
        modal: false,

        //API handler
        api: {
            baseUrl: window.location.origin+ '/',
            csrfToken: document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
            async HTTPget(endpoint) {
                console.log(this.baseUrl + endpoint);
            try {
                const res = await fetch(this.baseUrl + endpoint);
                if (!res.ok) throw new Error(`GET ${endpoint} failed`);
                return await res.json();
            } catch (err) {
                console.error(err);
                return {};
            }
            },
            async HTTPpost(endpoint, data) {
            try {
                const res = await fetch(this.baseUrl + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify(data)
                });
                if (!res.ok) throw new Error(`POST ${endpoint} failed`);
                return await res.json();
            } catch (err) {
                console.error(err);
                return {};
            }
            }
        },

    }
}

function smoothScrollTo(id) {
    const section = document.getElementById(id);
    if (section) {
        const sectionTop = section.getBoundingClientRect().top + window.pageYOffset - 100;
        window.scrollTo({
            top: sectionTop,
            behavior: 'smooth'
        });
    }
}

function countTokens(text) {
  const tokens = text.match(/\w+|[^\w\s]/gu) || [];
  let count = 0;

  for (const token of tokens) {
    if (token.length > 6) {
      // Long words often split into smaller tokens in LLMs
      count += Math.floor(token.length / 6) + 1;
    } else {
      count += 1;
    }
  }

  return count;
}

document.addEventListener('click', function (event) {
    if (event.target.tagName === 'A' && event.target.hash) {
        event.preventDefault();
        smoothScrollTo(event.target.hash.replace('#', ''));
    }
});

window.toast = function(message, options = {}){
    let description = '';
    let type = 'default';
    let position = 'top-center';
    let html = '';
    if(typeof options.description != 'undefined') description = options.description;
    if(typeof options.type != 'undefined') type = options.type;
    if(typeof options.position != 'undefined') position = options.position;
    if(typeof options.html != 'undefined') html = options.html;
    
    window.dispatchEvent(new CustomEvent('toast-show', { detail : { type: type, message: message, description: description, position : position, html: html }}));
}




function exportChart(chart, filetype) {

    const chartCanvas = document.getElementById(chart);
    const validFileTypes = ['jpg', 'png'];
    
    if (!validFileTypes.includes(filetype)) {
        console.error('Invalid file type');
        return;
    }

    const chartUrl = chartCanvas.toDataURL('image/' + filetype);
    const link = document.createElement('a');
    link.href = chartUrl;
    link.download = chart + '.' + filetype;
    link.click();
}