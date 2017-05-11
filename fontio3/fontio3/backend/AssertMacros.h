/*
 * AssertMacros.h
 *
 * Copyright (c) 2006 Monotype Imaging Inc. All Rights Reserved.
 * (for original change logs see outside sources)
 *
 */

/*
     File:       AssertMacros.h
 
     Contains:   This file defines structured error handling and assertion macros for
                 programming in C. Originally used in QuickDraw GX and later enhanced.
                 These macros are used throughout Apple's software.

                 See "Living In an Exceptional World" by Sean Parent
                 (develop, The Apple Technical Journal, Issue 11, August/September 1992)
                 <http://developer.apple.com/dev/techsupport/develop/issue11toc.shtml>
                 for the methodology behind these error handling and assertion macros.

     Copyright:  � 2002 by Apple Computer, Inc., all rights reserved.
  
     Bugs?:      For bug reports, consult the following page on
                 the World Wide Web:
 
                     http://developer.apple.com/bugreporter/ 
*/
#ifndef __ASSERTMACROS__
#define __ASSERTMACROS__


/*
 *  Macro overview:
 *  
 *      check(assertion)
 *         In production builds, pre-processed away  
 *         In debug builds, if assertion evaluates to false, calls DEBUG_ASSERT_MESSAGE
 *  
 *      verify(assertion)
 *         In production builds, evaluates assertion and does nothing
 *         In debug builds, if assertion evaluates to false, calls DEBUG_ASSERT_MESSAGE
 *  
 *      require(assertion, exceptionLabel)
 *         In production builds, if the assertion expression evaluates to false, goto exceptionLabel
 *         In debug builds, if the assertion expression evaluates to false, calls DEBUG_ASSERT_MESSAGE
 *                          and jumps to exceptionLabel
 *  
 *      In addition the following suffixes are available:
 * 
 *         _noerr     Adds "!= 0" to assertion.  Useful for asserting and OSStatus or OSErr is noErr (zero)
 *         _action    Adds statement to be executued if assertion fails
 *         _quiet     Suppress call to DEBUG_ASSERT_MESSAGE
 *         _string    Allows you to add explanitory message to DEBUG_ASSERT_MESSAGE
 *  
 *        For instance, require_noerr_string(resultCode, label, msg) will do nothing if 
 *        resultCode is zero, otherwise it will call DEBUG_ASSERT_MESSAGE with msg
 *        and jump to label.
 *
 *  Configuration:
 *
 *      By default all macros generate "production code" (i.e non-debug).  If  
 *      DEBUG_ASSERT_PRODUCTION_CODE is defined to zero or DEBUG is defined to non-zero
 *      while this header is included, the macros will generated debug code.
 *
 *      If DEBUG_ASSERT_COMPONENT_NAME_STRING is defined, all debug messages will
 *      be prefixed with it.
 *
 *      By default, all messages write to stderr.  If you would like to write a custom
 *      error message formater, defined DEBUG_ASSERT_MESSAGE to your function name.
 *
 */


/*
 *  Before including this file, #define DEBUG_ASSERT_COMPONENT_NAME_STRING to
 *  a C-string containing the name of your client. This string will be passed to
 *  the DEBUG_ASSERT_MESSAGE macro for inclusion in any assertion messages.
 *
 *  If you do not define DEBUG_ASSERT_COMPONENT_NAME_STRING, the default
 *  DEBUG_ASSERT_COMPONENT_NAME_STRING value, an empty string, will be used by
 *  the assertion macros.
 */
#ifndef DEBUG_ASSERT_COMPONENT_NAME_STRING
    #define DEBUG_ASSERT_COMPONENT_NAME_STRING ""
#endif


/*
 *  To activate the additional assertion code and messages for non-production builds,
 *  #define DEBUG_ASSERT_PRODUCTION_CODE to zero before including this file.
 *
 *  If you do not define DEBUG_ASSERT_PRODUCTION_CODE, the default value 1 will be used
 *  (production code = no assertion code and no messages).
 */
#ifndef DEBUG_ASSERT_PRODUCTION_CODE
   #define DEBUG_ASSERT_PRODUCTION_CODE !DEBUG
#endif


/*
 *  DEBUG_ASSERT_MESSAGE(component, assertion, label, error, file, line, errorCode)
 *
 *  Summary:
 *    All assertion messages are routed through this macro. If you wish to use your
 *    own routine to display assertion messages, you can override DEBUG_ASSERT_MESSAGE
 *    by #defining DEBUG_ASSERT_MESSAGE before including this file.
 *
 *  Parameters:
 *
 *    componentNameString:
 *      A pointer to a string constant containing the name of the
 *      component this code is part of. This must be a string constant
 *      (and not a string variable or NULL) because the preprocessor
 *      concatenates it with other string constants.
 *
 *    assertionString:
 *      A pointer to a string constant containing the assertion.
 *      This must be a string constant (and not a string variable or
 *      NULL) because the Preprocessor concatenates it with other
 *      string constants.
 *    
 *    exceptionLabelString:
 *      A pointer to a string containing the exceptionLabel, or NULL.
 *    
 *    errorString:
 *      A pointer to the error string, or NULL. DEBUG_ASSERT_MESSAGE macros
 *      must not attempt to concatenate this string with constant
 *      character strings.
 *    
 *    fileName:
 *      A pointer to the fileName or pathname (generated by the
 *      preprocessor __FILE__ identifier), or NULL.
 *    
 *    lineNumber:
 *      The line number in the file (generated by the preprocessor
 *      __LINE__ identifier), or 0 (zero).
 *    
 *    errorCode:
 *      A value associated with the assertion, or 0.
 *
 *  Here is an example of a DEBUG_ASSERT_MESSAGE macro and a routine which displays
 *  assertion messsages:
 *
 *      #define DEBUG_ASSERT_COMPONENT_NAME_STRING "MyCoolProgram"
 *
 *      #define DEBUG_ASSERT_MESSAGE(componentNameString, assertionString,                           \
 *                                   exceptionLabelString, errorString, fileName, lineNumber, errorCode) \
 *              MyProgramDebugAssert(componentNameString, assertionString,                           \
 *                                   exceptionLabelString, errorString, fileName, lineNumber, errorCode)
 *
 *      static void
 *      MyProgramDebugAssert(const char *componentNameString, const char *assertionString, 
 *                           const char *exceptionLabelString, const char *errorString, 
 *                           const char *fileName, long lineNumber, int errorCode)
 *      {
 *          if ( (assertionString != NULL) && (*assertionString != '\0') )
 *              fprintf(stderr, "Assertion failed: %s: %s\n", componentNameString, assertionString);
 *          else
 *              fprintf(stderr, "Check failed: %s:\n", componentNameString);
 *          if ( exceptionLabelString != NULL )
 *              fprintf(stderr, "    %s\n", exceptionLabelString);
 *          if ( errorString != NULL )
 *              fprintf(stderr, "    %s\n", errorString);
 *          if ( fileName != NULL )
 *              fprintf(stderr, "    file: %s\n", fileName);
 *          if ( lineNumber != 0 )
 *              fprintf(stderr, "    line: %ld\n", lineNumber);
 *          if ( errorCode != 0 )
 *              fprintf(stderr, "    error: %d\n", errorCode);
 *      }
 *
 *  If you do not define DEBUG_ASSERT_MESSAGE, a simple printf to stderr will be used.
 */
#ifndef DEBUG_ASSERT_MESSAGE
   #ifdef KERNEL
      #include <syslog.h>
      #define DEBUG_ASSERT_MESSAGE(name, assertion, label, message, file, line, value) \
                                  syslog(LOG_ERR, "AssertMacros: %s, %s file: %s, line: %d\n", assertion, (message!=0) ? message : "", file, line);
   #else
      #include <stdio.h>
      #define DEBUG_ASSERT_MESSAGE(name, assertion, label, message, file, line, value) \
                                  fprintf(stderr, "AssertMacros: %s, %s file: %s, line: %d\n", assertion, (message!=0) ? message : "", file, line);
   #endif
#endif





/*
 *  debug_string(message)
 *
 *  Summary:
 *    Production builds: does nothing and produces no code.
 *
 *    Non-production builds: call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    message:
 *      The C string to display.
 *
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define debug_string(message)
#else
   #define debug_string(message)                                              \
      do                                                                      \
      {                                                                       \
          DEBUG_ASSERT_MESSAGE(                                               \
              DEBUG_ASSERT_COMPONENT_NAME_STRING,                             \
              "",                                                             \
              0,                                                              \
              message,                                                        \
              __FILE__,                                                       \
              __LINE__,                                                       \
              0);                                                             \
      } while ( 0 )
#endif


/*
 *  check(assertion)
 *
 *  Summary:
 *    Production builds: does nothing and produces no code.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define check(assertion)
#else
   #define check(assertion)                                                   \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  0,                                                          \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
          }                                                                   \
      } while ( 0 )
#endif

#define ncheck(assertion)                                                     \
  check(!(assertion))


/*
 *  check_string(assertion, message)
 *
 *  Summary:
 *    Production builds: does nothing and produces no code.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define check_string(assertion, message)
#else
   #define check_string(assertion, message)                                   \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  0,                                                          \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
          }                                                                   \
      } while ( 0 )
#endif

#define ncheck_string(assertion, message)                                     \
  check_string(!(assertion), message)


/*
 *  check_noerr(errorCode)
 *
 *  Summary:
 *    Production builds: does nothing and produces no code.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The errorCode expression to compare with 0.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define check_noerr(errorCode)
#else
   #define check_noerr(errorCode)                                             \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  0,                                                          \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  check_noerr_string(errorCode, message)
 *
 *  Summary:
 *    Production builds: check_noerr_string() does nothing and produces
 *    no code.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The errorCode expression to compare to 0.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define check_noerr_string(errorCode, message)
#else
   #define check_noerr_string(errorCode, message)                             \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  0,                                                          \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  verify(assertion)
 *
 *  Summary:
 *    Production builds: evaluate the assertion expression, but ignore
 *    the result.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define verify(assertion)                                                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
          }                                                                   \
      } while ( 0 )
#else
   #define verify(assertion)                                                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  0,                                                          \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
          }                                                                   \
      } while ( 0 )
#endif

#define nverify(assertion)                                                    \
  verify(!(assertion))


/*
 *  verify_string(assertion, message)
 *
 *  Summary:
 *    Production builds: evaluate the assertion expression, but ignore
 *    the result.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define verify_string(assertion, message)                                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
          }                                                                   \
      } while ( 0 )
#else
   #define verify_string(assertion, message)                                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  0,                                                          \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
          }                                                                   \
      } while ( 0 )
#endif

#define nverify_string(assertion, message)                                    \
  verify_string(!(assertion), message)


/*
 *  verify_noerr(errorCode)
 *
 *  Summary:
 *    Production builds: evaluate the errorCode expression, but ignore
 *    the result.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define verify_noerr(errorCode)                                            \
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
          }                                                                   \
      } while ( 0 )
#else
   #define verify_noerr(errorCode)                                            \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  0,                                                          \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  verify_noerr_string(errorCode, message)
 *
 *  Summary:
 *    Production builds: evaluate the errorCode expression, but ignore
 *    the result.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define verify_noerr_string(errorCode, message)                            \
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
          }                                                                   \
      } while ( 0 )
#else
   #define verify_noerr_string(errorCode, message)                            \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  0,                                                          \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  verify_action(assertion, action)
 *
 *  Summary:
 *    Production builds: if the assertion expression evaluates to false,
 *    then execute the action statement or compound statement (block).
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE and then execute the action statement or compound
 *    statement (block).
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    action:
 *      The statement or compound statement (block).
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define verify_action(assertion, action)                                   \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              action;                                                         \
          }                                                                   \
      } while ( 0 )
#else
   #define verify_action(assertion, action)                                  \
     do                                                                      \
      {                                                                      \
          if ( !(assertion) )                                                \
          {                                                                  \
             DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                        \
                  #assertion,                                                \
                  0,                                                         \
                  0,                                                         \
                  __FILE__,                                                  \
                  __LINE__,                                                  \
                  0);                                                        \
             { action; }                                                     \
         }                                                                   \
     } while ( 0 )
#endif


/*
 *  require(assertion, exceptionLabel)
 *
 *  Summary:
 *    Production builds: if the assertion expression evaluates to false,
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require(assertion, exceptionLabel)                                 \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require(assertion, exceptionLabel)                                 \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  #exceptionLabel,                                            \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif

#define nrequire(assertion, exceptionLabel)                                   \
  require(!(assertion), exceptionLabel)


/*
 *  require_action(assertion, exceptionLabel, action)
 *
 *  Summary:
 *    Production builds: if the assertion expression evaluates to false,
 *    execute the action statement or compound statement (block) and then
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE, execute the action statement or compound
 *    statement (block), and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_action(assertion, exceptionLabel, action)                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_action(assertion, exceptionLabel, action)                  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  #exceptionLabel,                                            \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif

#define nrequire_action(assertion, exceptionLabel, action)                    \
  require_action(!(assertion), exceptionLabel, action)


/*
 *  require_quiet(assertion, exceptionLabel)
 *
 *  Summary:
 *    If the assertion expression evaluates to false, goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 */
#define require_quiet(assertion, exceptionLabel)                              \
  do                                                                          \
  {                                                                           \
      if ( !(assertion) )                                                     \
      {                                                                       \
          goto exceptionLabel;                                                \
      }                                                                       \
  } while ( 0 )

#define nrequire_quiet(assertion, exceptionLabel)                             \
  require_quiet(!(assertion), exceptionLabel)


/*
 *  require_action_quiet(assertion, exceptionLabel, action)
 *
 *  Summary:
 *    If the assertion expression evaluates to false, execute the action
 *    statement or compound statement (block), and goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 */
#define require_action_quiet(assertion, exceptionLabel, action)               \
  do                                                                          \
  {                                                                           \
      if ( !(assertion) )                                                     \
      {                                                                       \
          {                                                                   \
              action;                                                         \
          }                                                                   \
          goto exceptionLabel;                                                \
      }                                                                       \
  } while ( 0 )

#define nrequire_action_quiet(assertion, exceptionLabel, action)              \
  require_action_quiet(!(assertion), exceptionLabel, action)


/*
 *  require_string(assertion, exceptionLabel, message)
 *
 *  Summary:
 *    Production builds: if the assertion expression evaluates to false,
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE, and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_string(assertion, exceptionLabel, message)                 \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_string(assertion, exceptionLabel, message)                 \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  #exceptionLabel,                                            \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif

#define nrequire_string(assertion, exceptionLabel, string)                    \
  require_string(!(assertion), exceptionLabel, string)


/*
 *  require_action_string(assertion, exceptionLabel, action, message)
 *
 *  Summary:
 *    Production builds: if the assertion expression evaluates to false,
 *    execute the action statement or compound statement (block), and then
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the assertion expression evaluates to false,
 *    call DEBUG_ASSERT_MESSAGE, execute the action statement or compound
 *    statement (block), and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    assertion:
 *      The assertion expression.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_action_string(assertion, exceptionLabel, action, message)  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_action_string(assertion, exceptionLabel, action, message)  \
      do                                                                      \
      {                                                                       \
          if ( !(assertion) )                                                 \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #assertion,                                                 \
                  #exceptionLabel,                                            \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  0);                                                         \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif

#define nrequire_action_string(assertion, exceptionLabel, action, message)    \
  require_action_string(!(assertion), exceptionLabel, action, message)


/*
 *  require_noerr(errorCode, exceptionLabel)
 *
 *  Summary:
 *    Production builds: if the errorCode expression does not equal 0 (noErr),
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_noerr(errorCode, exceptionLabel)                           \
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_noerr(errorCode, exceptionLabel)                           \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  #exceptionLabel,                                            \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif

/*
 *  require_noerr_action(errorCode, exceptionLabel, action)
 *
 *  Summary:
 *    Production builds: if the errorCode expression does not equal 0 (noErr),
 *    execute the action statement or compound statement (block) and
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE, execute the action statement or
 *    compound statement (block), and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_noerr_action(errorCode, exceptionLabel, action)            \
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_noerr_action(errorCode, exceptionLabel, action)            \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  #exceptionLabel,                                            \
                  0,                                                          \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  require_noerr_quiet(errorCode, exceptionLabel)
 *
 *  Summary:
 *    If the errorCode expression does not equal 0 (noErr),
 *    goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 */
#define require_noerr_quiet(errorCode, exceptionLabel)                        \
  do                                                                          \
  {                                                                           \
      if ( 0 != (errorCode) )                                                 \
      {                                                                       \
          goto exceptionLabel;                                                \
      }                                                                       \
  } while ( 0 )


/*
 *  require_noerr_action_quiet(errorCode, exceptionLabel, action)
 *
 *  Summary:
 *    If the errorCode expression does not equal 0 (noErr),
 *    execute the action statement or compound statement (block) and
 *    goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 */
#define require_noerr_action_quiet(errorCode, exceptionLabel, action)         \
  do                                                                          \
  {                                                                           \
      if ( 0 != (errorCode) )                                                 \
      {                                                                       \
          {                                                                   \
              action;                                                         \
          }                                                                   \
          goto exceptionLabel;                                                \
      }                                                                       \
  } while ( 0 )


/*
 *  require_noerr_string(errorCode, exceptionLabel, message)
 *
 *  Summary:
 *    Production builds: if the errorCode expression does not equal 0 (noErr),
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE, and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_noerr_string(errorCode, exceptionLabel, message)           \
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_noerr_string(errorCode, exceptionLabel, message)           \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  #exceptionLabel,                                            \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif


/*
 *  require_noerr_action_string(errorCode, exceptionLabel, action, message)
 *
 *  Summary:
 *    Production builds: if the errorCode expression does not equal 0 (noErr),
 *    execute the action statement or compound statement (block) and
 *    goto exceptionLabel.
 *
 *    Non-production builds: if the errorCode expression does not equal 0 (noErr),
 *    call DEBUG_ASSERT_MESSAGE, execute the action statement or compound
 *    statement (block), and then goto exceptionLabel.
 *
 *  Parameters:
 *
 *    errorCode:
 *      The expression to compare to 0.
 *
 *    exceptionLabel:
 *      The label.
 *
 *    action:
 *      The statement or compound statement (block).
 *
 *    message:
 *      The C string to display.
 */
#if DEBUG_ASSERT_PRODUCTION_CODE
   #define require_noerr_action_string(errorCode, exceptionLabel, action, message)\
      do                                                                      \
      {                                                                       \
          if ( 0 != (errorCode) )                                             \
          {                                                                   \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#else
   #define require_noerr_action_string(errorCode, exceptionLabel, action, message) \
      do                                                                      \
      {                                                                       \
          int evalOnceErrorCode = (errorCode);                                \
          if ( 0 != evalOnceErrorCode )                                       \
          {                                                                   \
              DEBUG_ASSERT_MESSAGE(                                           \
                  DEBUG_ASSERT_COMPONENT_NAME_STRING,                         \
                  #errorCode " == 0 ",                                        \
                  #exceptionLabel,                                            \
                  message,                                                    \
                  __FILE__,                                                   \
                  __LINE__,                                                   \
                  evalOnceErrorCode);                                         \
              {                                                               \
                  action;                                                     \
              }                                                               \
              goto exceptionLabel;                                            \
          }                                                                   \
      } while ( 0 )
#endif


#endif /* __ASSERTMACROS__ */
