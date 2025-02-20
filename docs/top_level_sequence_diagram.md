# Top Level Sequence Diagram
Cover Agent consists of many classes but the fundamental flow lives within the CoverAgent and UnitTestGenerator classes. The following is a sequence diagram (written in [Mermaid](https://mermaid.js.org/syntax/sequenceDiagram.html)) depicting the flow of how Cover Agent works and interacts with a Large Language Model.

```mermaid
sequenceDiagram
    participant U as User
    participant M as main.py (CLI)
    participant CA as CoverAgent
    participant UTV as UnitTestValidator
    participant UTG as UnitTestGenerator
    participant CP as CoverageProcessor
    participant R as Runner
    participant AC as AgentCompletion (DefaultAgentCompletion)
    participant AI as AICaller (LLM)
    participant DB as UnitTestDB
    participant RG as ReportGenerator

    %% 1. User runs the CLI
    U->>M: python cover_agent/main.py [args]
    M->>CA: parse_args() <br/> → new CoverAgent(args)

    %% 2. CoverAgent initialization
    CA->>CA: _validate_paths()
    CA->>CA: _duplicate_test_file()
    CA->>CA: parse_command_to_run_only_a_single_test()

    note over CA: Creates supporting objects
    CA->>UTG: new UnitTestGenerator(...)
    CA->>UTV: new UnitTestValidator(...)

    %% 3. CoverAgent.run()
    CA->>CA: run()

    %% 3a. init() phase
    note over CA: init()
    CA->>UTV: initial_test_suite_analysis()
    UTV->>AC: analyze_suite_test_headers_indentation(...)
    AC->>AI: call_model()
    AI-->>AC: returns analysis response (YAML)
    AC-->>UTV: indentation & other info

    UTV->>AC: analyze_test_insert_line(...)
    AC->>AI: call_model()
    AI-->>AC: returns insert-line info (YAML)
    AC-->>UTV: line numbers to insert tests/imports

    note over UTV: store indentation<br/>and insertion lines

    %% 3b. get initial coverage
    UTV->>UTV: get_coverage()
    UTV->>UTV: run_coverage()
    UTV->>R: run_command(test_command)
    R-->>UTV: stdout, stderr, exit_code, time_of_test
    UTV->>CP: process_coverage_report(time_of_test)
    CP-->>UTV: coverage lines + coverage pct

    %% 4. run_test_gen()
    note over CA: Loop until coverage >= desired or<br/>we reach max iterations
    CA->>UTG: generate_tests()

    UTG->>AC: generate_tests(...)
    AC->>AI: call_model()
    AI-->>AC: returns new tests (YAML)
    AC-->>UTG: parse new_tests[]

    %% 5. For each generated test, validate
    loop For each new test
        CA->>UTV: validate_test(new_test)
        UTV->>R: run_command(test_command)
        R-->>UTV: returns exit_code, stderr, stdout

        alt Test fails or coverage not increased
            UTV->>UTV: rollback test file
            UTV->>UTV: record failure
        else Test passes & coverage improved
            UTV->>CP: run_coverage() → coverage
            CP-->>UTV: updated coverage
        end

        %% record each attempt in DB
        UTV->>DB: insert_attempt(test_result)
    end

    %% 6. Check coverage again to decide next iteration
    CA->>UTV: get_coverage()
    UTV->>UTV: run_coverage()
    UTV->>CP: process_coverage_report(...)
    CP-->>UTV: coverage lines + coverage pct

    note over CA: If coverage < desired then loop else done

    %% 7. Once done, generate HTML report
    CA->>DB: dump_to_report(report_filepath)
    DB->>RG: generate_report(results)
    RG-->>DB: returns

    note over CA: end
```