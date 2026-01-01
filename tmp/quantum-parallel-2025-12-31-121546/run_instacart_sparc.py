
import sys
sys.path.insert(0, "/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System")

try:
    from local_sparc_instacart import LocalSPARC
    sparc = LocalSPARC()
    
    # Try different method names
    if hasattr(sparc, 'run'):
        print("Using sparc.run()...")
        result = sparc.run("Build Instacart API client with authentication, search, and cart management")
    elif hasattr(sparc, 'execute'):
        print("Using sparc.execute()...")
        result = sparc.execute("Build Instacart API client with authentication, search, and cart management")
    elif hasattr(sparc, '__call__'):
        print("Using sparc()...")
        result = sparc("Build Instacart API client with authentication, search, and cart management")
    else:
        print(f"ERROR: No suitable method found. Available: {[m for m in dir(sparc) if not m.startswith('_')]}")
        sys.exit(1)
    
    print(f"\nSUCCESS! Generated {len(str(result))} characters")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
