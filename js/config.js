// js/config.js
export let DEFAULT_MODEL = null;
export const MAX_CONTEXT_WINDOW = 8192;

export function setDefaultModel(modelName) {
	if (modelName && typeof modelName === 'string') {
		DEFAULT_MODEL = modelName;
	}
}