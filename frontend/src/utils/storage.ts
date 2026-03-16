const TOKEN_KEY = 'eplan_access_token';
const PROJECT_KEY = 'eplan_selected_project';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (value: string) => localStorage.setItem(TOKEN_KEY, value);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

export const getStoredProjectId = () => {
  const value = localStorage.getItem(PROJECT_KEY);
  return value ? Number(value) : undefined;
};

export const setStoredProjectId = (projectId?: number) => {
  if (!projectId) {
    localStorage.removeItem(PROJECT_KEY);
    return;
  }
  localStorage.setItem(PROJECT_KEY, String(projectId));
};
