const UmbraState = {
    key: "umbra_v2_state",

    get() {
        const raw = localStorage.getItem(this.key);
        if (!raw) return {};
        try {
            return JSON.parse(raw);
        } catch {
            return {};
        }
    },

    set(state) {
        localStorage.setItem(this.key, JSON.stringify(state));
    },

    clear() {
        localStorage.removeItem(this.key);
    },

    updateLastPage(path) {
        const state = this.get();
        state.lastPage = path;
        this.set(state);
    },

    setFlag(flag) {
        const state = this.get();
        state.flags = state.flags || {};
        state.flags[flag] = true;
        this.set(state);
    },

    hasFlag(flag) {
        const state = this.get();
        return !!(state.flags && state.flags[flag]);
    }
};
