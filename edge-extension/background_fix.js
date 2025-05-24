/**
 * Stop periodic token checking
 */
function stopTokenChecking() {
    console.log('Stopping periodic token checking');
    if (self.tokenCheckIntervalId) {
        clearInterval(self.tokenCheckIntervalId);
        self.tokenCheckIntervalId = null;
    }
}
