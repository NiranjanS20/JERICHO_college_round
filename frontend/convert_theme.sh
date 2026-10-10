#!/bin/bash
FILES="src/pages/*.tsx src/components/*.tsx src/App.tsx"

for file in $FILES; do
  if [ -f "$file" ]; then
    # Skip LandingPage as it's already updated
    if [[ "$file" == *"LandingPage.tsx"* ]]; then
      continue
    fi

    # Text replacements
    sed -i '' 's/text-slate-900/text-[#1C1C1A]/g' $file
    sed -i '' 's/text-slate-800/text-[#1C1C1A]/g' $file
    sed -i '' 's/text-slate-700/text-[#1C1C1A]/g' $file
    sed -i '' 's/text-slate-600/text-[#5C5A56]/g' $file
    sed -i '' 's/text-slate-500/text-[#5C5A56]/g' $file
    sed -i '' 's/text-slate-400/text-[#8C8A85]/g' $file
    
    # Background replacements
    sed -i '' 's/bg-slate-50\/70/bg-[#F9F8F6]/g' $file
    sed -i '' 's/bg-slate-50/bg-[#F2F0EA]/g' $file
    sed -i '' 's/bg-slate-100\/80/bg-[#F2F0EA]/g' $file
    sed -i '' 's/bg-slate-100/bg-[#F2F0EA]/g' $file
    sed -i '' 's/bg-slate-200\/50/bg-[#EAE8E3]/g' $file
    
    # Border replacements
    sed -i '' 's/border-slate-200\/80/border-[#EAE8E3]/g' $file
    sed -i '' 's/border-slate-200\/60/border-[#EAE8E3]/g' $file
    sed -i '' 's/border-slate-200/border-[#EAE8E3]/g' $file
    sed -i '' 's/border-slate-300/border-[#D5D3CE]/g' $file

    # Indigo (Primary) replacements
    sed -i '' 's/bg-indigo-600/bg-[#1C1C1A]/g' $file
    sed -i '' 's/hover:bg-indigo-700/hover:bg-[#2A2A28]/g' $file
    sed -i '' 's/bg-indigo-700/bg-[#1C1C1A]/g' $file
    sed -i '' 's/text-indigo-600/text-[#1C1C1A]/g' $file
    sed -i '' 's/text-indigo-700/text-[#1C1C1A]/g' $file
    sed -i '' 's/border-indigo-600/border-[#1C1C1A]/g' $file
    sed -i '' 's/border-indigo-200/border-[#1C1C1A]\/20/g' $file
    sed -i '' 's/bg-indigo-50/bg-[#F2F0EA]/g' $file
    sed -i '' 's/shadow-indigo-600\/20/shadow-sm/g' $file

    # Emerald (Success) replacements
    sed -i '' 's/bg-emerald-50/bg-[#EAF2ED]/g' $file
    sed -i '' 's/bg-emerald-100/bg-[#D1E6DA]/g' $file
    sed -i '' 's/text-emerald-600/text-[#2E6A4F]/g' $file
    sed -i '' 's/text-emerald-700/text-[#2E6A4F]/g' $file
    sed -i '' 's/border-emerald-200/border-[#D1E6DA]/g' $file
    sed -i '' 's/bg-emerald-500/bg-[#2E6A4F]/g' $file

    # Rose (Failure) replacements
    sed -i '' 's/bg-rose-50/bg-[#FDF0ED]/g' $file
    sed -i '' 's/bg-rose-100/bg-[#F4D9D4]/g' $file
    sed -i '' 's/text-rose-600/text-[#9D3B31]/g' $file
    sed -i '' 's/text-rose-700/text-[#9D3B31]/g' $file
    sed -i '' 's/border-rose-200/border-[#F4D9D4]/g' $file

    # Amber (Warning) replacements
    sed -i '' 's/bg-amber-50/bg-[#FFF6E5]/g' $file
    sed -i '' 's/text-amber-600/text-[#9E6A00]/g' $file
    sed -i '' 's/text-amber-700/text-[#9E6A00]/g' $file
    sed -i '' 's/border-amber-200/border-[#FDE8B5]/g' $file
  fi
done
