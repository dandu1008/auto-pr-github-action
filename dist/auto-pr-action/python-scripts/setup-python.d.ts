/**
 * Setup for Python from the GitHub Actions tool cache
 * Converted from https://github.com/actions/setup-python
 *
 * @param {string} versionSpec version of Python
 * @param {string} arch architecture (x64|x32)
 */
export declare const setupPython: (versionSpec: string, arch: string) => Promise<unknown>;
