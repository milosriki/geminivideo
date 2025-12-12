#!/usr/bin/env python3
"""
Comprehensive Alignment Checker
Validates consistency across all scoring and ranking logic in the geminivideo project
"""

import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

class AlignmentChecker:
    # Tolerance for weight sum validation
    WEIGHT_SUM_TOLERANCE = 0.01
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.issues = []
        self.warnings = []
        self.info = []
        
    def check_all(self) -> bool:
        """Run all alignment checks"""
        print("=" * 80)
        print("GEMINIVIDEO ALIGNMENT CHECKER")
        print("=" * 80)
        print()
        
        self.check_config_files()
        self.check_weight_consistency()
        self.check_scoring_logic_alignment()
        self.check_shared_config_usage()
        
        self.print_report()
        
        return len(self.issues) == 0
    
    def check_config_files(self):
        """Check that all required config files exist and are valid"""
        print("📁 Checking Configuration Files...")
        
        config_path = self.root_path / "shared" / "config"
        required_files = [
            "weights.yaml",
            "scene_ranking.yaml",
            "triggers_config.json",
            "personas.json",
            "hook_templates.json"
        ]
        
        for filename in required_files:
            filepath = config_path / filename
            if not filepath.exists():
                self.issues.append(f"Missing config file: {filepath}")
            else:
                self.info.append(f"✓ Found {filename}")
                
                # Validate file can be parsed
                try:
                    if filename.endswith('.yaml'):
                        with open(filepath) as f:
                            yaml.safe_load(f)
                    elif filename.endswith('.json'):
                        with open(filepath) as f:
                            json.load(f)
                except Exception as e:
                    self.issues.append(f"Invalid format in {filename}: {e}")
        
        print()
    
    def check_weight_consistency(self):
        """Check that weights are consistent across configs"""
        print("⚖️  Checking Weight Consistency...")
        
        # Load weights.yaml
        weights_path = self.root_path / "shared" / "config" / "weights.yaml"
        scene_ranking_path = self.root_path / "shared" / "config" / "scene_ranking.yaml"
        
        try:
            with open(weights_path) as f:
                weights = yaml.safe_load(f)
            
            with open(scene_ranking_path) as f:
                scene_ranking = yaml.safe_load(f)
            
            # Check psychology weights sum
            psych_weights = weights.get('psychology_weights', {})
            psych_sum = sum(psych_weights.values())
            if abs(psych_sum - 1.0) > self.WEIGHT_SUM_TOLERANCE:
                self.warnings.append(f"Psychology weights sum to {psych_sum:.2f}, not 1.0")
            else:
                self.info.append(f"✓ Psychology weights sum to {psych_sum:.2f}")
            
            # Check hook weights sum
            hook_weights = weights.get('hook_weights', {})
            hook_sum = sum(hook_weights.values())
            if abs(hook_sum - 1.0) > self.WEIGHT_SUM_TOLERANCE:
                self.warnings.append(f"Hook weights sum to {hook_sum:.2f}, not 1.0")
            else:
                self.info.append(f"✓ Hook weights sum to {hook_sum:.2f}")
            
            # Check scene ranking weights sum
            ranking_weights = scene_ranking.get('weights', {})
            ranking_sum = sum(ranking_weights.values())
            if abs(ranking_sum - 1.0) > self.WEIGHT_SUM_TOLERANCE:
                self.warnings.append(f"Scene ranking weights sum to {ranking_sum:.2f}, not 1.0")
            else:
                self.info.append(f"✓ Scene ranking weights sum to {ranking_sum:.2f}")
            
        except Exception as e:
            self.issues.append(f"Error checking weight consistency: {e}")
        
        print()
    
    def check_scoring_logic_alignment(self):
        """Check that scoring logic is aligned across services"""
        print("🔍 Checking Scoring Logic Alignment...")
        
        # Check gateway-api scoring-engine.ts
        scoring_engine_path = self.root_path / "services" / "gateway-api" / "src" / "services" / "scoring-engine.ts"
        scoring_ts_path = self.root_path / "services" / "gateway-api" / "src" / "scoring.ts"
        
        if scoring_engine_path.exists():
            with open(scoring_engine_path) as f:
                content = f.read()
                
                # More robust pattern matching using regex
                import re
                
                # Look for the specific composite score calculation block
                # This is more targeted than catching all multiplications
                composite_pattern = r'const compositeScore\s*=\s*([\s\S]*?);'
                composite_match = re.search(composite_pattern, content)
                
                if composite_match:
                    composite_block = composite_match.group(1)
                    
                    # Now extract weights from this specific block
                    weight_pattern = r'(\w+Score)\s*\*\s*(0\.\d+)'
                    matches = re.findall(weight_pattern, composite_block)
                    
                    gateway_weights = {}
                    for var_name, weight_str in matches:
                        weight = float(weight_str)
                        gateway_weights[var_name] = weight
                        self.info.append(f"✓ Gateway uses {var_name} weight {weight}")
                    
                    # Verify sum if we found weights
                    if gateway_weights:
                        gateway_sum = sum(gateway_weights.values())
                        if abs(gateway_sum - 1.0) < self.WEIGHT_SUM_TOLERANCE:
                            self.info.append(f"✓ Gateway composite weights sum to {gateway_sum:.2f}")
                        else:
                            self.issues.append(f"Gateway composite weights sum to {gateway_sum:.2f}, not 1.0")
                    else:
                        self.warnings.append("Could not extract composite weights from gateway scoring-engine.ts")
                else:
                    self.warnings.append("Could not find compositeScore calculation in scoring-engine.ts")
        else:
            self.warnings.append("scoring-engine.ts not found")
        
        # Check drive-intel ranking.py
        ranking_path = self.root_path / "services" / "drive-intel" / "services" / "ranking.py"
        if ranking_path.exists():
            with open(ranking_path) as f:
                content = f.read()
                
                # Check if it references shared config
                if "self.weights.get" in content:
                    self.info.append("✓ Drive-intel uses configurable weights")
                else:
                    self.warnings.append("Drive-intel may have hardcoded weights")
        else:
            self.warnings.append("ranking.py not found in drive-intel")
        
        print()
    
    def check_shared_config_usage(self):
        """Check that services properly load shared config"""
        print("🔗 Checking Shared Config Usage...")
        
        # Check gateway-api
        gateway_index = self.root_path / "services" / "gateway-api" / "src" / "index.ts"
        if gateway_index.exists():
            with open(gateway_index) as f:
                content = f.read()
                if "weights.yaml" in content or "weightsPath" in content:
                    self.info.append("✓ Gateway loads weights.yaml")
                else:
                    self.warnings.append("Gateway may not load shared weights config")
        
        # Check drive-intel (check both main.py files)
        drive_main_paths = [
            self.root_path / "services" / "drive-intel" / "main.py",
            self.root_path / "services" / "drive-intel" / "src" / "main.py"
        ]
        
        found_config_load = False
        for drive_main in drive_main_paths:
            if drive_main.exists():
                with open(drive_main) as f:
                    content = f.read()
                    if "scene_ranking.yaml" in content:
                        self.info.append(f"✓ Drive-intel ({drive_main.name}) loads scene_ranking.yaml")
                        found_config_load = True
                        break
        
        if not found_config_load:
            self.warnings.append("Drive-intel may not load shared ranking config")
        
        print()
    
    def print_report(self):
        """Print comprehensive report"""
        print("=" * 80)
        print("ALIGNMENT CHECK REPORT")
        print("=" * 80)
        print()
        
        if self.info:
            print("ℹ️  Information:")
            for item in self.info:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("⚠️  Warnings:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.issues:
            print("❌ Issues:")
            for item in self.issues:
                print(f"  {item}")
            print()
        else:
            print("✅ No critical issues found!")
            print()
        
        print("=" * 80)
        print(f"Summary: {len(self.issues)} issues, {len(self.warnings)} warnings")
        print("=" * 80)


def main():
    root_path = Path(__file__).parent.parent
    checker = AlignmentChecker(root_path)
    
    success = checker.check_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
