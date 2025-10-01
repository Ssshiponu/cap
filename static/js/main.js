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