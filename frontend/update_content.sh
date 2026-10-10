#!/bin/bash
FILES="src/pages/*.tsx src/components/*.tsx src/App.tsx"

for file in $FILES; do
  if [ -f "$file" ]; then
    # --- Color Replacements ---
    # Backgrounds
    sed -i '' 's/#F9F8F6/#FFFAED/g' $file
    sed -i '' 's/#F2F0EA/#FFFFFF/g' $file
    # Text / Primary Dark
    sed -i '' 's/#1C1C1A/#275992/g' $file
    sed -i '' 's/#2A2A28/#1C4370/g' $file
    # Borders / Muted
    sed -i '' 's/#EAE8E3/#95A1D8/g' $file
    sed -i '' 's/#D5D3CE/#95A1D8/g' $file
    sed -i '' 's/#8C8A85/#95A1D8/g' $file
    sed -i '' 's/#5C5A56/#275992/g' $file
    
    # Status colors (Force them to the new palette)
    # Success / Resisted -> Atlantic Blue
    sed -i '' 's/#2E6A4F/#275992/g' $file
    sed -i '' 's/#EAF2ED/#FFFAED/g' $file
    sed -i '' 's/#D1E6DA/#95A1D8/g' $file
    # Failure / Breached -> Dusty Iris
    sed -i '' 's/#9D3B31/#95A1D8/g' $file
    sed -i '' 's/#FDF0ED/#FFFFFF/g' $file
    sed -i '' 's/#F4D9D4/#95A1D8/g' $file
    # Warning
    sed -i '' 's/#9E6A00/#275992/g' $file
    sed -i '' 's/#FFF6E5/#FFFAED/g' $file

    # Typography classes
    sed -i '' 's/font-serif-elegant/font-heading/g' $file
    sed -i '' 's/font-sans-clean/font-body/g' $file

    # --- Copy Replacements (No AI) ---
    sed -i '' 's/AgentBreak/Platform/g' $file
    sed -i '' 's/Agent/System/g' $file
    sed -i '' 's/agent/system/g' $file
    sed -i '' 's/AI/Automated/g' $file
    sed -i '' 's/Red-Team/Validation/g' $file
    sed -i '' 's/red-team/validation/g' $file
    sed -i '' 's/Red-Teamer/Validator/g' $file
    sed -i '' 's/LLMs/Workflows/g' $file
    sed -i '' 's/LLM/Workflow/g' $file
    sed -i '' 's/autonomous/automated/g' $file
    sed -i '' 's/Autonomous/Automated/g' $file
    sed -i '' 's/Attack/Probe/g' $file
    sed -i '' 's/attack/probe/g' $file
    sed -i '' 's/Attacker/Tester/g' $file
    sed -i '' 's/attacker/tester/g' $file
    sed -i '' 's/malicious/anomalous/g' $file
    sed -i '' 's/Malicious/Anomalous/g' $file
    sed -i '' 's/Exploit/Test/g' $file
    sed -i '' 's/exploit/test/g' $file
    sed -i '' 's/Mutation/Iteration/g' $file
    sed -i '' 's/mutation/iteration/g' $file
    sed -i '' 's/Victim/Target/g' $file
  fi
done
