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

document.addEventListener('click', function (event) {
    if (event.target.tagName === 'A' && event.target.hash) {
        event.preventDefault();
        smoothScrollTo(event.target.hash.replace('#', ''));
    }
});
