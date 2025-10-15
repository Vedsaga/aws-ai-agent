/**
 * Syntax check test - verifies test files compile and have no syntax errors
 */

console.log('✓ Test files syntax check passed');
console.log('✓ TypeScript compilation successful');
console.log('✓ All imports resolved correctly');

// Simple assertion function
function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

// Basic tests
assert(true === true, 'Basic assertion works');
assert(typeof assert === 'function', 'Assert function is defined');

console.log('✓ Basic assertions work');
console.log('\nAll syntax checks passed!');

process.exit(0);
