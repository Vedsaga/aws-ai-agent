# Quick Test Checklist

Use this checklist to quickly verify all features are working. For detailed instructions, see `infrastructure/frontend/MANUAL_TESTING_GUIDE.md`.

## Prerequisites
- [ ] Backend APIs are deployed and accessible
- [ ] Frontend is running (`npm run dev` in `infrastructure/frontend`)
- [ ] User is logged in with valid credentials
- [ ] Environment variables are set in `.env.local`

## Quick Tests

### 1. Agent CRUD (5 min)
- [ ] Navigate to `/agents` page
- [ ] Click "Create Agent" and create a test agent
- [ ] Verify agent appears in list with "Created by me" tag
- [ ] Click "Edit" and modify the agent
- [ ] Click "Delete" and confirm deletion
- [ ] Verify built-in agents don't have Edit/Delete buttons

### 2. Domain Creation (5 min)
- [ ] Navigate to `/manage` page
- [ ] Click "Create Domain" button
- [ ] Enter domain name and description
- [ ] Select 2 ingestion agents in Stage 1
- [ ] Verify dependency graph shows parallel execution
- [ ] Click "Next" to proceed to Stage 2
- [ ] Select 3 query agents
- [ ] Verify dependency graph updates
- [ ] Click "Create Domain"
- [ ] Verify domain appears in list

### 3. Real-time Status (3 min)
- [ ] Navigate to dashboard
- [ ] Select a domain from dropdown
- [ ] Enter report text and click "Submit Report"
- [ ] Verify ExecutionStatusPanel appears
- [ ] Watch agents show "invoking" status with spinner
- [ ] Verify agents show "complete" with confidence badges
- [ ] Verify confidence badges are color-coded (green >= 90%, red < 90%)

### 4. Clarification (5 min)
- [ ] Submit report with ambiguous text: "Pothole on Main Street"
- [ ] Wait for processing to complete
- [ ] Verify ClarificationDialog appears if confidence < 90%
- [ ] Enter clarification details
- [ ] Click "Submit Clarification"
- [ ] Verify report is re-processed
- [ ] Verify confidence improves

### 5. Geometry Rendering (5 min)
- [ ] Submit report: "Broken streetlight at 123 Main St"
- [ ] Navigate to map view
- [ ] Verify Point marker appears
- [ ] Submit report: "Road construction from Main St to Oak Ave"
- [ ] Verify LineString (line) appears
- [ ] Submit report: "Flooding in the downtown area"
- [ ] Verify Polygon (filled area) appears
- [ ] Click on each geometry type to verify popups work

### 6. Network Errors (3 min)
- [ ] Refresh page 5 times
- [ ] Verify no "NetworkError" toasts appear
- [ ] Open DevTools → Network tab → Set to "Offline"
- [ ] Try to submit a report
- [ ] Verify appropriate error toast appears
- [ ] Set back to "Online"
- [ ] Submit report again
- [ ] Verify it succeeds

## Pass Criteria

All checkboxes should be checked (✓) for the feature to be considered working.

## If Tests Fail

1. Check browser console for errors
2. Verify environment variables are set
3. Verify backend APIs are accessible
4. Check network tab for failed requests
5. Review detailed testing guide: `infrastructure/frontend/MANUAL_TESTING_GUIDE.md`
6. Document bugs using the bug tracking template

## Automated Test

For Agent CRUD operations, you can also run:

```bash
cd infrastructure/frontend
TEST_JWT_TOKEN="your-token-here" node test-agent-crud.js
```

This will automatically test all agent CRUD operations and provide a pass/fail report.

## Time Estimate

- **Quick Test:** ~25 minutes
- **Comprehensive Test:** ~2 hours (using full manual testing guide)
- **Automated Test:** ~2 minutes

## Success Indicators

✅ All checkboxes are checked  
✅ No console errors  
✅ No network errors on page refresh  
✅ All features work as expected  
✅ User experience is smooth and intuitive

## Next Steps After Testing

1. Document any bugs found
2. Prioritize critical issues
3. Fix bugs one by one
4. Re-test after each fix
5. Update this checklist if needed

---

**Last Updated:** October 20, 2025  
**Status:** Ready for Testing
