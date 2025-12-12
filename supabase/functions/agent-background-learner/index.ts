// Background Learning Cron - Learns from your ENTIRE app hourly
// Unlimited learning - discovers new tables, functions, and patterns automatically

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.0";

const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY")!;
const supabase = createClient(supabaseUrl, supabaseKey);

Deno.serve(async (req) => {
  try {
    console.log("🚀 Starting unlimited learning cycle...");

    // 1. Rediscover structure (all tables + functions)
    console.log("📊 Discovering app structure...");
    const { data: tables, error: tablesError } = await supabase.rpc("get_all_tables");
    
    if (tablesError) {
      console.error("❌ Table discovery failed:", tablesError);
      throw tablesError;
    }

    const { data: functions, error: functionsError } = await supabase.rpc("get_all_functions");
    
    if (functionsError) {
      console.error("❌ Function discovery failed:", functionsError);
      throw functionsError;
    }

    console.log(`✅ Discovered ${tables?.length || 0} tables, ${functions?.length || 0} functions`);

    // 2. Learn recent changes (last 24 hours)
    console.log("📈 Learning recent changes...");
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    
    const recentData = await Promise.all([
      supabase
        .from("campaign_performance")
        .select("*")
        .gte("created_at", yesterday)
        .limit(100),
      supabase
        .from("lead_tracking")
        .select("*")
        .gte("created_at", yesterday)
        .limit(100),
      supabase
        .from("daily_metrics")
        .select("*")
        .gte("created_at", yesterday)
        .limit(100),
      supabase
        .from("videos")
        .select("*")
        .gte("created_at", yesterday)
        .limit(100),
      supabase
        .from("campaigns")
        .select("*")
        .gte("created_at", yesterday)
        .limit(100),
    ]);

    // 3. Extract patterns
    const patterns = {
      campaign_performance: {
        count: recentData[0].data?.length || 0,
        recent_statuses: [...new Set(recentData[0].data?.map((r: any) => r.performance_status) || [])],
        avg_roas: recentData[0].data?.reduce((sum: number, r: any) => sum + (r.roas || 0), 0) / (recentData[0].data?.length || 1),
      },
      lead_tracking: {
        count: recentData[1].data?.length || 0,
        sources: [...new Set(recentData[1].data?.map((r: any) => r.lead_source) || [])],
        avg_lead_score: recentData[1].data?.reduce((sum: number, r: any) => sum + (r.lead_score || 0), 0) / (recentData[1].data?.length || 1),
      },
      daily_metrics: {
        count: recentData[2].data?.length || 0,
        avg_spend: recentData[2].data?.reduce((sum: number, r: any) => sum + (r.total_spend || 0), 0) / (recentData[2].data?.length || 1),
      },
      videos: {
        count: recentData[3].data?.length || 0,
        platforms: [...new Set(recentData[3].data?.map((r: any) => r.platform) || [])],
      },
      campaigns: {
        count: recentData[4].data?.length || 0,
        statuses: [...new Set(recentData[4].data?.map((r: any) => r.status) || [])],
      },
    };

    // 4. Build knowledge object
    const knowledge = {
      structure: {
        tables: tables?.map((t: any) => ({
          name: t.table_name,
          row_count: t.row_count,
          rls_enabled: t.rls_enabled,
        })) || [],
        functions: functions?.map((f: any) => ({
          name: f.function_name,
          return_type: f.return_type,
        })) || [],
      },
      recent_changes: {
        total_new_records: recentData.reduce((sum, r) => sum + (r.data?.length || 0), 0),
        patterns,
      },
      discovered_at: new Date().toISOString(),
    };

    // 5. Save to agent memory
    console.log("💾 Saving to agent memory...");
    const { error: saveError } = await supabase.from("agent_memory").insert({
      key: `daily_learning_${Date.now()}`,
      value: knowledge,
      type: "daily_discovery",
      metadata: {
        tables_discovered: tables?.length || 0,
        functions_discovered: functions?.length || 0,
        recent_records: recentData.reduce((sum, r) => sum + (r.data?.length || 0), 0),
      },
    });

    if (saveError) {
      console.error("❌ Failed to save learning:", saveError);
      throw saveError;
    }

    console.log("✅ Unlimited learning complete!");
    console.log(`   - Tables: ${tables?.length || 0}`);
    console.log(`   - Functions: ${functions?.length || 0}`);
    console.log(`   - Recent records: ${recentData.reduce((sum, r) => sum + (r.data?.length || 0), 0)}`);

    return new Response(
      JSON.stringify({
        success: true,
        message: "Unlimited learning complete",
        discovered: {
          tables: tables?.length || 0,
          functions: functions?.length || 0,
          recent_records: recentData.reduce((sum, r) => sum + (r.data?.length || 0), 0),
        },
      }),
      {
        headers: { "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error: any) {
    console.error("❌ Learning error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message || "Unknown error",
      }),
      {
        headers: { "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});

